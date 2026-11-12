import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

enum LoginResult { success, registrationNotApproved, invalidCredentials }

class AuthService {
  final ApiService _api = ApiService();
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  static const String _tokenKey = 'auth_token';

  Future<LoginResult> login(String email, String password) async {
    try {
      final response = await _api.post('/api/v1/auth/deliverer/login', {
        'email': email,
        'password': password,
      });
      final token = response['access_token'] as String?;
      if (token != null) {
        await _storage.write(key: _tokenKey, value: token);
        return LoginResult.success;
      }
      return LoginResult.invalidCredentials;
    } on DioException catch (e) {
      final code = e.response?.data?['error'] as String?;
      if (code == 'REGISTRATION_NOT_APPROVED') {
        return LoginResult.registrationNotApproved;
      }
      return LoginResult.invalidCredentials;
    } catch (_) {
      return LoginResult.invalidCredentials;
    }
  }

  Future<bool> register(Map<String, dynamic> data) async {
    try {
      await _api.post('/api/v1/auth/deliverer/register', data);
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<String?> registerError(Map<String, dynamic> data) async {
    try {
      await _api.post('/api/v1/auth/deliverer/register', data);
      return null;
    } on DioException catch (e) {
      return e.response?.data?['message'] as String? ?? 'Erro ao cadastrar.';
    } catch (_) {
      return 'Erro ao cadastrar.';
    }
  }

  Future<void> logout() async {
    await _storage.delete(key: _tokenKey);
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: _tokenKey);
    return token != null && token.isNotEmpty;
  }

  Future<String?> getToken() async {
    return _storage.read(key: _tokenKey);
  }
}
