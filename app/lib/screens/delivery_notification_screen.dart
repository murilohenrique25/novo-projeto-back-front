import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// Screen shown when a delivery notification arrives.
/// Displays pickup address, destination address, and fee.
/// Allows the deliverer to accept the delivery.
class DeliveryNotificationScreen extends StatefulWidget {
  final Map<String, dynamic> notification;

  const DeliveryNotificationScreen({super.key, required this.notification});

  @override
  State<DeliveryNotificationScreen> createState() =>
      _DeliveryNotificationScreenState();
}

class _DeliveryNotificationScreenState
    extends State<DeliveryNotificationScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  Future<void> _acceptDelivery() async {
    final deliveryId = widget.notification['delivery_id'] as String?;
    if (deliveryId == null) return;

    setState(() => _isLoading = true);

    try {
      final result = await _apiService.post(
        '/api/v1/deliverer/deliveries/$deliveryId/accept',
        {},
      );

      if (!mounted) return;

      // Navigate to delivery execution screen with delivery data
      Navigator.pushReplacementNamed(
        context,
        '/delivery_execution',
        arguments: result,
      );
    } catch (e) {
      if (!mounted) return;

      final errorMessage = _extractErrorMessage(e);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(errorMessage)));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _extractErrorMessage(Object e) {
    final str = e.toString();
    if (str.contains('DELIVERY_ALREADY_TAKEN')) {
      return 'Entrega já foi aceita por outro entregador';
    }
    return 'Erro ao aceitar entrega. Tente novamente.';
  }

  @override
  Widget build(BuildContext context) {
    final n = widget.notification;
    final fee = (n['fee'] as num?)?.toDouble() ?? 0.0;

    return Scaffold(
      appBar: AppBar(title: const Text('Nova Entrega')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
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
                    const SizedBox(height: 4),
                    Text(
                      n['pickup_address'] as String? ?? '-',
                      style: const TextStyle(fontSize: 16),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Destino',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      n['destination_address'] as String? ?? '-',
                      style: const TextStyle(fontSize: 16),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Taxa',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'R\$ ${fee.toStringAsFixed(2)}',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.green,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const Spacer(),
            ElevatedButton(
              onPressed: _isLoading ? null : _acceptDelivery,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
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
                      : const Text(
                        'Aceitar Entrega',
                        style: TextStyle(fontSize: 16),
                      ),
            ),
          ],
        ),
      ),
    );
  }
}
