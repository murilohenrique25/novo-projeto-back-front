import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _loading = false;

  // Shown inline when registration is pending/rejected
  String? _registrationStatusMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _registrationStatusMessage = null;
    });

    final auth = context.read<AuthService>();
    final result = await auth.login(
      _emailController.text.trim(),
      _passwordController.text,
    );

    if (!mounted) return;
    setState(() => _loading = false);

    switch (result) {
      case LoginResult.success:
        Navigator.pushReplacementNamed(context, '/home');
      case LoginResult.registrationNotApproved:
        // Show inline status message (pending or rejected)
        setState(() {
          _registrationStatusMessage =
              'Seu cadastro ainda não foi aprovado. '
              'Aguarde a análise ou verifique se foi rejeitado.';
        });
      case LoginResult.invalidCredentials:
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('E-mail ou senha inválidos.'),
            backgroundColor: Colors.red,
          ),
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                controller: _emailController,
                decoration: const InputDecoration(labelText: 'E-mail'),
                keyboardType: TextInputType.emailAddress,
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Informe o e-mail' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                decoration: const InputDecoration(labelText: 'Senha'),
                obscureText: true,
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Informe a senha' : null,
              ),
              if (_registrationStatusMessage != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.orange.shade50,
                    border: Border.all(color: Colors.orange),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline, color: Colors.orange),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _registrationStatusMessage!,
                          style: const TextStyle(color: Colors.orange),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 24),
              _loading
                  ? const CircularProgressIndicator()
                  : SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _submit,
                      child: const Text('Entrar'),
                    ),
                  ),
              TextButton(
                onPressed: () => Navigator.pushNamed(context, '/register'),
                child: const Text('Criar conta'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
