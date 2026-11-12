import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _cpfController = TextEditingController();
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _cityIdController = TextEditingController();
  final _documentPhotoController = TextEditingController();
  bool _loading = false;
  bool _submitted = false;

  @override
  void dispose() {
    _nameController.dispose();
    _cpfController.dispose();
    _phoneController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _cityIdController.dispose();
    _documentPhotoController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _submitted = false;
    });

    final auth = context.read<AuthService>();
    final error = await auth.registerError({
      'full_name': _nameController.text.trim(),
      'cpf': _cpfController.text.trim(),
      'phone': _phoneController.text.trim(),
      'email': _emailController.text.trim(),
      'password': _passwordController.text,
      'city_id': _cityIdController.text.trim(),
      'document_photo': _documentPhotoController.text.trim(),
    });

    if (!mounted) return;
    setState(() => _loading = false);

    if (error == null) {
      setState(() => _submitted = true);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error), backgroundColor: Colors.red),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_submitted) {
      return Scaffold(
        appBar: AppBar(title: const Text('Cadastro de Entregador')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 64),
              const SizedBox(height: 16),
              const Text(
                'Cadastro enviado! Aguarde aprovação.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 18),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Voltar ao login'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Cadastro de Entregador')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(labelText: 'Nome completo'),
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cpfController,
                decoration: const InputDecoration(labelText: 'CPF'),
                keyboardType: TextInputType.number,
                maxLength: 11,
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Obrigatório';
                  if (v.length != 11) return 'CPF deve ter 11 dígitos';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _phoneController,
                decoration: const InputDecoration(labelText: 'Telefone'),
                keyboardType: TextInputType.phone,
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _emailController,
                decoration: const InputDecoration(labelText: 'E-mail'),
                keyboardType: TextInputType.emailAddress,
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _passwordController,
                decoration: const InputDecoration(labelText: 'Senha'),
                obscureText: true,
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _cityIdController,
                decoration: const InputDecoration(
                  labelText: 'ID da Cidade (UUID)',
                  hintText: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
                ),
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _documentPhotoController,
                decoration: const InputDecoration(
                  labelText: 'Foto do Documento (URL)',
                  hintText: 'https://...',
                ),
                keyboardType: TextInputType.url,
                validator:
                    (v) => (v == null || v.isEmpty) ? 'Obrigatório' : null,
              ),
              const SizedBox(height: 24),
              _loading
                  ? const CircularProgressIndicator()
                  : SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _submit,
                      child: const Text('Cadastrar'),
                    ),
                  ),
            ],
          ),
        ),
      ),
    );
  }
}
