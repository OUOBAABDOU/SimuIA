import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';

import 'models/interview.dart';
import 'models/media.dart';
import 'services/api.dart';
import 'services/livekit_service.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

void main() => runApp(IarhApp(api: Api(apiBaseUrl)));

class IarhApp extends StatelessWidget {
  const IarhApp({super.key, required this.api});
  final Api api;

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'IARH — AI Career Growth Coach',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
      useMaterial3: true,
    ),
    home: FutureBuilder<bool>(
      future: api.isAuthenticated(),
      builder: (context, snapshot) =>
          snapshot.data == true ? Home(api: api) : Login(api: api),
    ),
  );
}

class Login extends StatefulWidget {
  const Login({super.key, required this.api});
  final Api api;
  @override
  State<Login> createState() => _LoginState();
}

class _LoginState extends State<Login> {
  final email = TextEditingController();
  final password = TextEditingController();
  final firstName = TextEditingController();
  final lastName = TextEditingController();
  final domain = TextEditingController();
  final targetRole = TextEditingController();
  final phone = TextEditingController();
  final location = TextEditingController();
  bool busy = false;
  bool registering = false;
  String? error;

  Future<void> submit() async {
    if (registering && password.text.length < 12) {
      setState(() => error = 'Password must contain at least 12 characters.');
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      if (registering) {
        await widget.api.register(
          email: email.text.trim(),
          password: password.text,
          firstName: firstName.text.trim(),
          lastName: lastName.text.trim(),
          domain: domain.text.trim(),
          targetRole: targetRole.text.trim(),
          phone: phone.text,
          location: location.text,
        );
      }
      await widget.api.login(email.text.trim(), password.text);
      if (mounted)
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => Home(api: widget.api)),
        );
    } catch (_) {
      if (mounted)
        setState(
          () => error = registering
              ? 'Unable to create this account.'
              : 'Invalid credentials or unavailable server.',
        );
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  void dispose() {
    for (final controller in [
      email,
      password,
      firstName,
      lastName,
      domain,
      targetRole,
      phone,
      location,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 420),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'IARH',
                style: TextStyle(fontSize: 34, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                registering
                    ? 'Create your candidate account'
                    : 'AI Career Growth Coach',
              ),
              const SizedBox(height: 28),
              TextField(
                controller: email,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(labelText: 'Email'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: password,
                obscureText: true,
                decoration: const InputDecoration(labelText: 'Password'),
              ),
              if (registering) ...[
                const SizedBox(height: 12),
                TextField(
                  controller: firstName,
                  decoration: const InputDecoration(labelText: 'First name'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: lastName,
                  decoration: const InputDecoration(labelText: 'Last name'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: domain,
                  decoration: const InputDecoration(
                    labelText: 'Professional domain',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: targetRole,
                  decoration: const InputDecoration(labelText: 'Target role'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Phone (optional)',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: location,
                  decoration: const InputDecoration(
                    labelText: 'Location (optional)',
                  ),
                ),
              ],
              if (error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(
                    error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: busy ? null : submit,
                child: busy
                    ? const CircularProgressIndicator()
                    : Text(registering ? 'Create account' : 'Sign in'),
              ),
              TextButton(
                onPressed: busy
                    ? null
                    : () => setState(() {
                        registering = !registering;
                        error = null;
                      }),
                child: Text(
                  registering
                      ? 'Already have an account? Sign in'
                      : 'New here? Create an account',
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

class Home extends StatefulWidget {
  const Home({super.key, required this.api});
  final Api api;
  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  late Future<List<dynamic>> interviews;
  @override
  void initState() {
    super.initState();
    interviews = widget.api.interviews();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const Text('My interviews'),
      actions: [
        IconButton(
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => NewSimulation(api: widget.api)),
          ),
          icon: const Icon(Icons.add),
          tooltip: 'New interview',
        ),
        IconButton(
          onPressed: () async {
            await widget.api.logout();
            if (mounted)
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (_) => Login(api: widget.api)),
              );
          },
          icon: const Icon(Icons.logout),
        ),
      ],
    ),
    body: FutureBuilder<List<dynamic>>(
      future: interviews,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting)
          return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError)
          return const Center(child: Text('Unable to load interviews.'));
        final items = snapshot.data ?? [];
        if (items.isEmpty)
          return const Center(child: Text('No interviews yet.'));
        return RefreshIndicator(
          onRefresh: () async =>
              setState(() => interviews = widget.api.interviews()),
          child: ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = InterviewSummary.fromJson(
                Map<String, dynamic>.from(items[index]),
              );
              return ListTile(
                leading: const Icon(Icons.record_voice_over),
                title: Text('Interview ${item.id.substring(0, 8)}'),
                subtitle: Text(
                  '${item.status} • question ${item.currentQuestionIndex + 1}',
                ),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        InterviewDetail(api: widget.api, interview: item),
                  ),
                ),
              );
            },
          ),
        );
      },
    ),
  );
}

class NewSimulation extends StatefulWidget {
  const NewSimulation({super.key, required this.api});
  final Api api;

  @override
  State<NewSimulation> createState() => _NewSimulationState();
}

class _NewSimulationState extends State<NewSimulation> {
  final role = TextEditingController();
  final domain = TextEditingController();
  final questions = TextEditingController(text: '5');
  bool busy = false;
  String? error;

  @override
  void dispose() {
    role.dispose();
    domain.dispose();
    questions.dispose();
    super.dispose();
  }

  Future<void> create() async {
    final count = int.tryParse(questions.text);
    if (role.text.trim().isEmpty ||
        domain.text.trim().isEmpty ||
        count == null ||
        count < 1 ||
        count > 20) {
      setState(
        () =>
            error = 'Complete the fields; questions must be between 1 and 20.',
      );
      return;
    }
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final simulation = await widget.api.createSimulation(
        role: role.text.trim(),
        domain: domain.text.trim(),
        totalQuestions: count,
      );
      final interview = await widget.api.createInterview(
        simulation['id'] as String,
      );
      await widget.api.startInterview(interview['id'] as String);
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (_) => InterviewSession(
              api: widget.api,
              interviewId: interview['id'] as String,
            ),
          ),
        );
      }
    } catch (_) {
      if (mounted) setState(() => error = 'Unable to create the interview.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('New interview')),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        TextField(
          controller: role,
          decoration: const InputDecoration(labelText: 'Target role'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: domain,
          decoration: const InputDecoration(labelText: 'Professional domain'),
        ),
        const SizedBox(height: 12),
        TextField(
          controller: questions,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Number of questions'),
        ),
        if (error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: Text(
              error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: busy ? null : create,
          child: busy
              ? const CircularProgressIndicator()
              : const Text('Start interview'),
        ),
      ],
    ),
  );
}

class InterviewSession extends StatefulWidget {
  const InterviewSession({
    super.key,
    required this.api,
    required this.interviewId,
  });
  final Api api;
  final String interviewId;

  @override
  State<InterviewSession> createState() => _InterviewSessionState();
}

class _InterviewSessionState extends State<InterviewSession> {
  final answer = TextEditingController();
  final liveKit = LiveKitService();
  late Future<Map<String, dynamic>> question;
  bool busy = false;
  bool joined = false;
  bool evidenceConsent = false;
  String? error;

  @override
  void initState() {
    super.initState();
    question = widget.api.currentQuestion(widget.interviewId);
  }

  @override
  void dispose() {
    answer.dispose();
    liveKit.disconnect();
    super.dispose();
  }

  Future<void> joinRoom() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.consent(widget.interviewId);
      final data = await widget.api.joinInterview(widget.interviewId);
      await liveKit.connect(
        serverUrl: data['server_url'] as String,
        token: data['token'] as String,
      );
      await liveKit.setCameraEnabled(false);
      await liveKit.setMicrophoneEnabled(false);
      if (mounted) setState(() => joined = true);
    } catch (_) {
      if (mounted) setState(() => error = 'Unable to join the interview room.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> submitAnswer(Map<String, dynamic> current) async {
    if (answer.text.trim().isEmpty) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      await widget.api.answerQuestion(
        widget.interviewId,
        current['id'] as String,
        answer.text.trim(),
      );
      answer.clear();
      setState(() => question = widget.api.currentQuestion(widget.interviewId));
    } catch (_) {
      if (mounted) setState(() => error = 'Unable to submit this answer.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> finish() async {
    setState(() => busy = true);
    try {
      await widget.api.finishInterview(widget.interviewId);
      await liveKit.disconnect();
      if (mounted) Navigator.pop(context);
    } catch (_) {
      if (mounted)
        setState(() => error = 'Answer all questions before finishing.');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Interview session')),
    body: FutureBuilder<Map<String, dynamic>>(
      future: question,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting)
          return const Center(child: CircularProgressIndicator());
        if (snapshot.hasError || !snapshot.hasData)
          return Center(child: Text(error ?? 'No question available.'));
        final current = snapshot.data!;
        return ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text(
              current['prompt'] as String,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 20),
            if (!joined)
              CheckboxListTile(
                value: evidenceConsent,
                onChanged: busy
                    ? null
                    : (value) => setState(() => evidenceConsent = value ?? false),
                title: const Text('Data-use and evidence consent'),
                subtitle: const Text(
                  'I agree that my recording, transcript and anonymized usage '
                  'evidence may be shared with authorized evaluators. I can '
                  'decline and stop before joining the room.',
                ),
                controlAffinity: ListTileControlAffinity.leading,
              ),
            if (!joined)
              OutlinedButton.icon(
                onPressed: busy || !evidenceConsent ? null : joinRoom,
                icon: const Icon(Icons.videocam),
                label: const Text('Accept and join room'),
              ),
            if (joined)
              const Text(
                'Room connected. Camera and microphone are disabled until enabled.',
              ),
            const SizedBox(height: 20),
            TextField(
              controller: answer,
              minLines: 5,
              maxLines: 10,
              decoration: const InputDecoration(
                labelText: 'Your answer',
                border: OutlineInputBorder(),
              ),
            ),
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(
                  error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: busy ? null : () => submitAnswer(current),
              child: const Text('Submit answer'),
            ),
            TextButton(
              onPressed: busy ? null : finish,
              child: const Text('Finish interview'),
            ),
          ],
        );
      },
    ),
  );
}

class InterviewDetail extends StatefulWidget {
  const InterviewDetail({
    super.key,
    required this.api,
    required this.interview,
  });
  final Api api;
  final InterviewSummary interview;
  @override
  State<InterviewDetail> createState() => _InterviewDetailState();
}

class _InterviewDetailState extends State<InterviewDetail> {
  late Future<List<dynamic>> recordings;
  Report? report;
  Transcript? transcript;

  @override
  void initState() {
    super.initState();
    recordings = widget.api.recordings(widget.interview.id);
    loadReport();
  }

  Future<void> loadReport() async {
    try {
      report = Report.fromJson(await widget.api.report(widget.interview.id));
    } catch (_) {}
    if (mounted) setState(() {});
  }

  Future<void> loadTranscript(Recording recording) async {
    try {
      final data = await widget.api.transcript(
        widget.interview.id,
        recording.id,
      );
      if (mounted) setState(() => transcript = Transcript.fromJson(data));
    } catch (_) {}
  }

  Future<void> play(Recording recording) async {
    final url = await widget.api.recordingUrl(
      widget.interview.id,
      recording.id,
    );
    if (mounted)
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => MediaPlayer(url: url, title: recording.kind),
        ),
      );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Interview report')),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: ListTile(
            title: const Text('Status'),
            subtitle: Text(widget.interview.status),
          ),
        ),
        if (report != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Gemini report',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  Text(
                    'Overall score: ${report!.globalScore.toStringAsFixed(1)}/100',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(report!.summary),
                  const SizedBox(height: 8),
                  Text('Strengths: ${report!.strengths.join(' • ')}'),
                  Text('Improve: ${report!.weaknesses.join(' • ')}'),
                  Text('Next steps: ${report!.recommendations.join(' • ')}'),
                ],
              ),
            ),
          ),
        const SizedBox(height: 12),
        Text('Recordings', style: Theme.of(context).textTheme.titleLarge),
        FutureBuilder<List<dynamic>>(
          future: recordings,
          builder: (context, snapshot) {
            if (!snapshot.hasData)
              return const Center(child: CircularProgressIndicator());
            final items = snapshot.data!
                .map((x) => Recording.fromJson(Map<String, dynamic>.from(x)))
                .toList();
            return Column(
              children: items
                  .map(
                    (recording) => Card(
                      child: ListTile(
                        title: Text(recording.kind),
                        subtitle: Text(recording.status),
                        trailing: Wrap(
                          children: [
                            IconButton(
                              onPressed: recording.status == 'READY'
                                  ? () => loadTranscript(recording)
                                  : null,
                              icon: const Icon(Icons.article),
                            ),
                            IconButton(
                              onPressed: recording.status == 'READY'
                                  ? () => play(recording)
                                  : null,
                              icon: const Icon(Icons.play_circle),
                            ),
                          ],
                        ),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
        ),
        if (transcript != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(transcript!.text),
            ),
          ),
      ],
    ),
  );
}

class MediaPlayer extends StatefulWidget {
  const MediaPlayer({super.key, required this.url, required this.title});
  final String url;
  final String title;
  @override
  State<MediaPlayer> createState() => _MediaPlayerState();
}

class _MediaPlayerState extends State<MediaPlayer> {
  late final VideoPlayerController controller;
  @override
  void initState() {
    super.initState();
    controller = VideoPlayerController.networkUrl(Uri.parse(widget.url))
      ..initialize().then((_) {
        if (mounted) setState(() {});
      });
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text(widget.title)),
    body: Center(
      child: controller.value.isInitialized
          ? AspectRatio(
              aspectRatio: controller.value.aspectRatio,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  VideoPlayer(controller),
                  IconButton(
                    icon: Icon(
                      controller.value.isPlaying
                          ? Icons.pause_circle
                          : Icons.play_circle,
                      size: 64,
                      color: Colors.white,
                    ),
                    onPressed: () {
                      setState(() {
                        controller.value.isPlaying
                            ? controller.pause()
                            : controller.play();
                      });
                    },
                  ),
                ],
              ),
            )
          : const CircularProgressIndicator(),
    ),
  );
}
