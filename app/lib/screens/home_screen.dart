import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';

/// Decodes the payload section of a JWT token without verifying the signature.
Map<String, dynamic> _decodeJwtPayload(String token) {
  final parts = token.split('.');
  if (parts.length != 3) return {};
  // Base64url decode with padding
  String payload = parts[1];
  final remainder = payload.length % 4;
  if (remainder != 0) {
    payload = payload.padRight(payload.length + (4 - remainder), '=');
  }
  final decoded = utf8.decode(base64Url.decode(payload));
  return jsonDecode(decoded) as Map<String, dynamic>;
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final AuthService _authService = AuthService();
  final WebSocketService _wsService = WebSocketService();
  final ApiService _apiService = ApiService();

  bool _isActive = false;
  StreamSubscription<Position>? _positionSubscription;
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;

  // Incoming delivery notifications (for the list)
  final List<Map<String, dynamic>> _notifications = [];

  // Track which delivery_id has an open notification dialog
  String? _openNotificationDeliveryId;

  @override
  void initState() {
    super.initState();
    _initWebSocket();
  }

  Future<void> _initWebSocket() async {
    final token = await _authService.getToken();
    if (token == null) return;

    final payload = _decodeJwtPayload(token);
    final delivererId = payload['sub'] as String? ?? payload['id'] as String?;
    if (delivererId == null) return;

    const wsBase = 'ws://10.0.2.2:8000/ws/deliverer';
    _wsService.connect('$wsBase/$delivererId', token);

    _wsSubscription = _wsService.messages.listen((msg) {
      if (msg['type'] == 'delivery_notification') {
        setState(() => _notifications.insert(0, msg));
        _showDeliveryNotificationDialog(msg);
      } else if (msg['type'] == 'delivery_cancelled') {
        final cancelledId = msg['delivery_id'] as String?;
        if (cancelledId != null && cancelledId == _openNotificationDeliveryId) {
          _dismissOpenNotificationDialog();
        }
      }
    });
  }

  void _showDeliveryNotificationDialog(Map<String, dynamic> notification) {
    if (!mounted) return;
    final deliveryId = notification['delivery_id'] as String?;
    _openNotificationDeliveryId = deliveryId;

    showModalBottomSheet<void>(
      context: context,
      isDismissible: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder:
          (ctx) => _DeliveryNotificationSheet(
            notification: notification,
            apiService: _apiService,
            onAccepted: (deliveryData) {
              _openNotificationDeliveryId = null;
              Navigator.pop(ctx);
              Navigator.pushNamed(
                context,
                '/delivery_execution',
                arguments: deliveryData,
              );
            },
            onError: (message) {
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(SnackBar(content: Text(message)));
            },
          ),
    ).whenComplete(() {
      if (_openNotificationDeliveryId == deliveryId) {
        _openNotificationDeliveryId = null;
      }
    });
  }

  void _dismissOpenNotificationDialog() {
    if (mounted && _openNotificationDeliveryId != null) {
      _openNotificationDeliveryId = null;
      Navigator.of(context, rootNavigator: true).maybePop();
    }
  }

  Future<void> _toggleStatus() async {
    final newActive = !_isActive;
    setState(() => _isActive = newActive);

    if (newActive) {
      _wsService.sendJson({'type': 'status_change', 'status': 'active'});
      _startGps();
    } else {
      _wsService.sendJson({'type': 'status_change', 'status': 'inactive'});
      _stopGps();
    }
  }

  void _startGps() {
    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 0,
    );

    _positionSubscription = Geolocator.getPositionStream(
      locationSettings: locationSettings,
    ).listen((Position position) {
      final now = DateTime.now().toUtc().toIso8601String();
      _wsService.sendJson({
        'type': 'location_update',
        'lat': position.latitude,
        'lng': position.longitude,
        'timestamp': now,
      });
    });

    // Enforce 10-second interval by throttling via a periodic timer approach:
    // geolocator streams continuously; we rely on distanceFilter=0 and the
    // backend's TTL of 35s. For strict 10s intervals we wrap with a timer.
    _positionSubscription?.cancel();
    _positionSubscription = null;
    _startPeriodicGps();
  }

  void _startPeriodicGps() {
    // Send location every 10 seconds while active
    Timer.periodic(const Duration(seconds: 10), (timer) async {
      if (!_isActive) {
        timer.cancel();
        return;
      }
      try {
        final position = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
        );
        final now = DateTime.now().toUtc().toIso8601String();
        _wsService.sendJson({
          'type': 'location_update',
          'lat': position.latitude,
          'lng': position.longitude,
          'timestamp': now,
        });
      } catch (_) {
        // GPS unavailable — skip this tick
      }
    });
  }

  void _stopGps() {
    _positionSubscription?.cancel();
    _positionSubscription = null;
  }

  Future<void> _logout() async {
    _stopGps();
    _wsService.disconnect();
    await _authService.logout();
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  void dispose() {
    _stopGps();
    _wsSubscription?.cancel();
    _wsService.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Início'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sair',
            onPressed: _logout,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status toggle
            Card(
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _isActive ? 'Ativo' : 'Inativo',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: _isActive ? Colors.green : Colors.grey,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Switch(
                      value: _isActive,
                      activeColor: Colors.green,
                      onChanged: (_) => _toggleStatus(),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Notificações de entrega',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Expanded(
              child:
                  _notifications.isEmpty
                      ? const Center(
                        child: Text(
                          'Nenhuma notificação no momento.',
                          style: TextStyle(color: Colors.grey),
                        ),
                      )
                      : ListView.builder(
                        itemCount: _notifications.length,
                        itemBuilder: (context, index) {
                          final n = _notifications[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: const Icon(
                                Icons.delivery_dining,
                                color: Colors.blue,
                              ),
                              title: Text(
                                'Coleta: ${n['pickup_address'] ?? '-'}',
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Destino: ${n['destination_address'] ?? '-'}',
                                  ),
                                  Text(
                                    'Taxa: R\$ ${(n['fee'] ?? 0).toStringAsFixed(2)}',
                                  ),
                                  if (n['city'] != null)
                                    Text('Cidade: ${n['city']}'),
                                ],
                              ),
                              isThreeLine: true,
                            ),
                          );
                        },
                      ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Bottom sheet widget for displaying a delivery notification and accepting it.
class _DeliveryNotificationSheet extends StatefulWidget {
  final Map<String, dynamic> notification;
  final ApiService apiService;
  final void Function(Map<String, dynamic> deliveryData) onAccepted;
  final void Function(String message) onError;

  const _DeliveryNotificationSheet({
    required this.notification,
    required this.apiService,
    required this.onAccepted,
    required this.onError,
  });

  @override
  State<_DeliveryNotificationSheet> createState() =>
      _DeliveryNotificationSheetState();
}

class _DeliveryNotificationSheetState
    extends State<_DeliveryNotificationSheet> {
  bool _isLoading = false;

  Future<void> _accept() async {
    final deliveryId = widget.notification['delivery_id'] as String?;
    if (deliveryId == null) return;

    setState(() => _isLoading = true);
    try {
      final result = await widget.apiService.post(
        '/api/v1/deliverer/deliveries/$deliveryId/accept',
        {},
      );
      if (mounted) widget.onAccepted(result);
    } catch (e) {
      if (!mounted) return;
      final msg =
          e.toString().contains('DELIVERY_ALREADY_TAKEN')
              ? 'Entrega já foi aceita por outro entregador'
              : 'Erro ao aceitar entrega. Tente novamente.';
      widget.onError(msg);
      Navigator.pop(context);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final n = widget.notification;
    final fee = (n['fee'] as num?)?.toDouble() ?? 0.0;

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Nova Entrega Disponível',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          _InfoRow(
            label: 'Coleta',
            value: n['pickup_address'] as String? ?? '-',
          ),
          const SizedBox(height: 8),
          _InfoRow(
            label: 'Destino',
            value: n['destination_address'] as String? ?? '-',
          ),
          const SizedBox(height: 8),
          _InfoRow(
            label: 'Taxa',
            value: 'R\$ ${fee.toStringAsFixed(2)}',
            valueStyle: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: Colors.green,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _isLoading ? null : _accept,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.green,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child:
                _isLoading
                    ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                    : const Text('Aceitar', style: TextStyle(fontSize: 16)),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  final TextStyle? valueStyle;

  const _InfoRow({required this.label, required this.value, this.valueStyle});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 60,
          child: Text(
            '$label:',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
        ),
        Expanded(child: Text(value, style: valueStyle)),
      ],
    );
  }
}
