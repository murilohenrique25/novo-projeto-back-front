class Deliverer {
  final String id;
  final String fullName;
  final String cpf;
  final String phone;
  final String email;
  final String cityId;
  final String regStatus;
  final String? rejectionReason;
  final bool isActive;
  final double balance;

  Deliverer({
    required this.id,
    required this.fullName,
    required this.cpf,
    required this.phone,
    required this.email,
    required this.cityId,
    required this.regStatus,
    this.rejectionReason,
    required this.isActive,
    required this.balance,
  });

  factory Deliverer.fromJson(Map<String, dynamic> json) {
    return Deliverer(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      cpf: json['cpf'] as String,
      phone: json['phone'] as String,
      email: json['email'] as String,
      cityId: json['city_id'] as String,
      regStatus: json['reg_status'] as String,
      rejectionReason: json['rejection_reason'] as String?,
      isActive: json['is_active'] as bool? ?? false,
      balance: (json['balance'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'full_name': fullName,
      'cpf': cpf,
      'phone': phone,
      'email': email,
      'city_id': cityId,
      'reg_status': regStatus,
      'rejection_reason': rejectionReason,
      'is_active': isActive,
      'balance': balance,
    };
  }
}
