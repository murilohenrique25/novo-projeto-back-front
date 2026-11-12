import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  final StreamController<Map<String, dynamic>> _controller =
      StreamController<Map<String, dynamic>>.broadcast();

  /// Connects to [url] appending [token] as a query parameter.
  void connect(String url, String token) {
    final uri = Uri.parse('$url?token=$token');
    _channel = WebSocketChannel.connect(uri);
    _channel!.stream.listen(
      (data) {
        try {
          final decoded = jsonDecode(data as String) as Map<String, dynamic>;
          _controller.add(decoded);
        } catch (_) {
          // ignore malformed messages
        }
      },
      onError: (error) => _controller.addError(error),
      onDone: () {},
    );
  }

  /// Sends a JSON-encoded message over the WebSocket.
  void sendJson(Map<String, dynamic> data) {
    _channel?.sink.add(jsonEncode(data));
  }

  /// Stream of parsed JSON messages received from the server.
  Stream<Map<String, dynamic>> get messages => _controller.stream;

  /// Closes the WebSocket connection.
  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }
}
