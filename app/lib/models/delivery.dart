class Delivery {
  final String id;
  final String companyId;
  final String cityId;
  final String? delivererId;
  final String pickupAddress;
  final double pickupLat;
  final double pickupLng;
  final String destinationAddress;
  final double destinationLat;
  final double destinationLng;
  final double radiusKm;
  final double fee;
  final double platformCut;
  final double delivererCut;
  final String status;
  final String? acceptedAt;
  final String? pickedUpAt;
  final String? completedAt;
  final String createdAt;

  Delivery({
    required this.id,
    required this.companyId,
    required this.cityId,
    this.delivererId,
    required this.pickupAddress,
    required this.pickupLat,
    required this.pickupLng,
    required this.destinationAddress,
    required this.destinationLat,
    required this.destinationLng,
    required this.radiusKm,
    required this.fee,
    required this.platformCut,
    required this.delivererCut,
    required this.status,
    this.acceptedAt,
    this.pickedUpAt,
    this.completedAt,
    required this.createdAt,
  });

  factory Delivery.fromJson(Map<String, dynamic> json) {
    return Delivery(
      id: json['id'] as String,
      companyId: json['company_id'] as String,
      cityId: json['city_id'] as String,
      delivererId: json['deliverer_id'] as String?,
      pickupAddress: json['pickup_address'] as String,
      pickupLat: (json['pickup_lat'] as num).toDouble(),
      pickupLng: (json['pickup_lng'] as num).toDouble(),
      destinationAddress: json['destination_address'] as String,
      destinationLat: (json['destination_lat'] as num).toDouble(),
      destinationLng: (json['destination_lng'] as num).toDouble(),
      radiusKm: (json['radius_km'] as num).toDouble(),
      fee: (json['fee'] as num).toDouble(),
      platformCut: (json['platform_cut'] as num).toDouble(),
      delivererCut: (json['deliverer_cut'] as num).toDouble(),
      status: json['status'] as String,
      acceptedAt: json['accepted_at'] as String?,
      pickedUpAt: json['picked_up_at'] as String?,
      completedAt: json['completed_at'] as String?,
      createdAt: json['created_at'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'company_id': companyId,
      'city_id': cityId,
      'deliverer_id': delivererId,
      'pickup_address': pickupAddress,
      'pickup_lat': pickupLat,
      'pickup_lng': pickupLng,
      'destination_address': destinationAddress,
      'destination_lat': destinationLat,
      'destination_lng': destinationLng,
      'radius_km': radiusKm,
      'fee': fee,
      'platform_cut': platformCut,
      'deliverer_cut': delivererCut,
      'status': status,
      'accepted_at': acceptedAt,
      'picked_up_at': pickedUpAt,
      'completed_at': completedAt,
      'created_at': createdAt,
    };
  }
}
