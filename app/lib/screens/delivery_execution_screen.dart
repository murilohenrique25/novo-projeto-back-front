import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

class DeliveryExecutionScreen extends StatefulWidget {
  const DeliveryExecutionScreen({super.key});

  @override
  State<DeliveryExecutionScreen> createState() =>
      _DeliveryExecutionScreenState();
}

class _DeliveryExecutionScreenState extends State<DeliveryExecutionScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  String _deliveryState = 'waiting_pickup';
  Map<String, dynamic> _delivery = {};

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is Map<String, dynamic>) {
      _delivery = args;
    }
  }

  Future<void> _confirmPickup() async {
    final deliveryId = _delivery['id'] as String?;
    if (deliveryId == null) return;
    setState(() => _isLoading = true);
    try {
      await _apiService.post(
        '/api/v1/deliverer/deliveries/$deliveryId/pickup',
        {},
      );
      if (!mounted) return;
      setState(() => _deliveryState = 'picked_up');
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erro ao confirmar coleta.')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _openGoogleMaps() async {
    final destLat = _delivery['destination_lat'];
    final destLng = _delivery['destination_lng'];
    final uri = Uri.parse(
      'https://www.google.com/maps/dir/?api=1&destination=$destLat,$destLng',
    );
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível abrir o Google Maps.')),
      );
    }
  }

  Future<void> _confirmDelivery() async {
    final deliveryId = _delivery['id'] as String?;
    if (deliveryId == null) return;
    setState(() => _isLoading = true);
    try {
      await _apiService.post(
        '/api/v1/deliverer/deliveries/$deliveryId/complete',
        {},
      );
      if (!mounted) return;
      setState(() => _deliveryState = 'completed');
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Erro ao confirmar entrega.')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _goHome() {
    Navigator.pushReplacementNamed(context, '/home');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Execução da Entrega')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    switch (_deliveryState) {
      case 'waiting_pickup':
        return _buildWaitingPickup();
      case 'picked_up':
        return _buildPickedUp();
      case 'completed':
        return _buildCompleted();
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildWaitingPickup() {
    final pickupAddress = _delivery['pickup_address'] as String? ?? '-';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Ponto de Coleta',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 8),
                Text(pickupAddress, style: const TextStyle(fontSize: 16)),
              ],
            ),
          ),
        ),
        const Spacer(),
        ElevatedButton(
          onPressed: _isLoading ? null : _confirmPickup,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.blue,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Text('Confirmar Coleta', style: TextStyle(fontSize: 16)),
        ),
      ],
    );
  }

  Widget _buildPickedUp() {
    final destinationAddress =
        _delivery['destination_address'] as String? ?? '-';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Destino',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.grey,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 8),
                Text(destinationAddress, style: const TextStyle(fontSize: 16)),
              ],
            ),
          ),
        ),
        const Spacer(),
        OutlinedButton.icon(
          onPressed: _openGoogleMaps,
          icon: const Icon(Icons.map),
          label:
              const Text('Abrir Google Maps', style: TextStyle(fontSize: 16)),
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
        const SizedBox(height: 12),
        ElevatedButton(
          onPressed: _isLoading ? null : _confirmDelivery,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.green,
            foregroundColor: Colors.white,
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: Colors.white,
                  ),
                )
              : const Text('Confirmar Entrega', style: TextStyle(fontSize: 16)),
        ),
      ],
    );
  }

  Widget _buildCompleted() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(Icons.check_circle, color: Colors.green, size: 80),
        const SizedBox(height: 24),
        const Text(
          'Entrega concluída!',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 48),
        ElevatedButton(
          onPressed: _goHome,
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
          child: const Text('Voltar ao início', style: TextStyle(fontSize: 16)),
        ),
      ],
    );
  }
}
