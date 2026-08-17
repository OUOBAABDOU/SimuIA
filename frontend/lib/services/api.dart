import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class Api {
  static const _secure = FlutterSecureStorage();
  final Dio dio;
  Api(String baseUrl)
    : dio = Dio(
        BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 20),
        ),
      ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (o, h) async {
          final t = await _secure.read(key: 'access_token');
          if (t != null) o.headers['Authorization'] = 'Bearer $t';
          h.next(o);
        },
        onError: (e, h) async {
          if (e.response?.statusCode == 401 &&
              !e.requestOptions.path.endsWith('/auth/refresh')) {
            final r = await _secure.read(key: 'refresh_token');
            if (r != null) {
              try {
                final x = await dio.post(
                  '/api/v1/auth/refresh',
                  data: {'refresh_token': r},
                );
                await _secure.write(
                  key: 'access_token',
                  value: x.data['access_token'],
                );
                await _secure.write(
                  key: 'refresh_token',
                  value: x.data['refresh_token'],
                );
                final retry = await dio.fetch(
                  e.requestOptions
                    ..headers['Authorization'] =
                        'Bearer ${x.data['access_token']}',
                );
                return h.resolve(retry);
              } catch (_) {}
            }
          }
          h.next(e);
        },
      ),
    );
  }
  Future<bool> isAuthenticated() async =>
      await _secure.read(key: 'access_token') != null;
  Future<void> register({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
    required String domain,
    required String targetRole,
    String? phone,
    String? location,
  }) async {
    await dio.post(
      '/api/v1/auth/register',
      data: {
        'email': email,
        'password': password,
        'first_name': firstName,
        'last_name': lastName,
        'domain': domain,
        'target_role': targetRole,
        if (phone != null && phone.trim().isNotEmpty) 'phone': phone.trim(),
        if (location != null && location.trim().isNotEmpty)
          'location': location.trim(),
      },
    );
  }

  Future<void> login(String email, String password) async {
    final r = await dio.post(
      '/api/v1/auth/login',
      data: {'email': email, 'password': password},
    );
    await _secure.write(key: 'access_token', value: r.data['access_token']);
    await _secure.write(key: 'refresh_token', value: r.data['refresh_token']);
  }

  Future<void> changePassword(
    String currentPassword,
    String newPassword,
  ) async {
    await dio.post(
      '/api/v1/auth/change-password',
      data: {'current_password': currentPassword, 'new_password': newPassword},
    );
    await _secure.deleteAll();
  }

  Future<Map<String, dynamic>> requestPasswordReset(String email) async =>
      (await dio.post(
        '/api/v1/auth/request-password-reset',
        data: {'email': email},
      )).data;

  Future<void> resetPassword(String token, String newPassword) async {
    await dio.post(
      '/api/v1/auth/reset-password',
      data: {'token': token, 'new_password': newPassword},
    );
  }

  Future<void> logout() async {
    final r = await _secure.read(key: 'refresh_token');
    if (r != null) {
      try {
        await dio.post('/api/v1/auth/logout', data: {'refresh_token': r});
      } catch (_) {}
    }
    await _secure.deleteAll();
  }

  Future<List<dynamic>> interviews() async =>
      (await dio.get('/api/v1/interviews')).data;
  Future<Map<String, dynamic>> createSimulation({
    required String role,
    required String domain,
    required int totalQuestions,
    String category = 'entretien_embauche',
    String experienceLevel = 'intermediate',
    String interviewStyle = 'structured',
    String mode = 'text',
  }) async => (await dio.post(
    '/api/v1/simulations',
    data: {
      'category': category,
      'sector': domain,
      'role': role,
      'experience_level': experienceLevel,
      'interview_style': interviewStyle,
      'mode': mode,
      'total_questions': totalQuestions,
    },
  )).data;
  Future<Map<String, dynamic>> createInterview(String simulationId) async =>
      (await dio.post(
        '/api/v1/interviews',
        data: {'simulation_id': simulationId},
      )).data;
  Future<Map<String, dynamic>> startInterview(String interviewId) async =>
      (await dio.post('/api/v1/interviews/$interviewId/start')).data;
  Future<Map<String, dynamic>> currentQuestion(String interviewId) async =>
      (await dio.get('/api/v1/interviews/$interviewId/current-question')).data;
  Future<Map<String, dynamic>> answerQuestion(
    String interviewId,
    String questionId,
    String text,
  ) async => (await dio.post(
    '/api/v1/interviews/$interviewId/questions/$questionId/answer',
    data: {'answer_type': 'TEXT', 'text': text},
  )).data;
  Future<Map<String, dynamic>> finishInterview(String interviewId) async =>
      (await dio.post('/api/v1/interviews/$interviewId/finish')).data;
  Future<void> consent(String interviewId) async => dio.post(
    '/api/v1/interviews/$interviewId/consent',
    data: {'accepted': true},
  );
  Future<List<dynamic>> progress() async =>
      (await dio.get('/api/v1/interviews/progress')).data;
  Future<void> giveRecordingConsent(String interviewId) async => dio.post(
    '/api/v1/interviews/$interviewId/consent',
    data: {'accepted': true},
  );
  Future<Map<String, dynamic>> joinInterview(String id) async =>
      (await dio.post('/api/v1/interviews/$id/join')).data;
  Future<List<dynamic>> recordings(String id) async =>
      (await dio.get('/api/v1/interviews/$id/recordings')).data;
  Future<Map<String, dynamic>> report(String id) async =>
      (await dio.get('/api/v1/interviews/$id/report')).data;
  Future<Map<String, dynamic>> transcript(
    String interviewId,
    String recordingId,
  ) async => (await dio.get(
    '/api/v1/interviews/$interviewId/transcripts/$recordingId',
  )).data;
  Future<String> recordingUrl(String interviewId, String recordingId) async =>
      (await dio.get(
        '/api/v1/interviews/$interviewId/recordings/$recordingId/download',
      )).data['url'];
}
