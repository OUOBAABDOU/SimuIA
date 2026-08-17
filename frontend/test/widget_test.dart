import 'package:flutter_test/flutter_test.dart';
import 'package:iarh_frontend/main.dart';
import 'package:iarh_frontend/services/api.dart';

void main() {
  testWidgets('IARH app renders', (tester) async {
    final api = Api('http://localhost:8000');
    await tester.pumpWidget(IarhApp(api: api));
    await tester.pump();
    expect(find.text('IARH'), findsOneWidget);
  });

  test('API smoke contract uses a root base URL', () {
    final api = Api('http://localhost:8000');
    expect(api.dio.options.baseUrl, 'http://localhost:8000');
    expect(api.dio.options.baseUrl, isNot(contains('/api/v1')));
  });
}
