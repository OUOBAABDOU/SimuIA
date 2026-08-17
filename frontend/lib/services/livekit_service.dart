import 'package:livekit_client/livekit_client.dart';

/// Owns the LiveKit room lifecycle for an interview.
/// Tokens are issued by FastAPI; this client never contains LiveKit secrets.
class LiveKitService {
  Room? _room;

  Room? get room => _room;

  Future<Room> connect({
    required String serverUrl,
    required String token,
  }) async {
    await disconnect();
    final room = Room();
    await room.connect(serverUrl, token);
    _room = room;
    return room;
  }

  Future<void> setCameraEnabled(bool enabled) async {
    final room = _room;
    if (room == null) throw StateError('LiveKit room is not connected');
    final participant = room.localParticipant;
    if (participant == null)
      throw StateError('LiveKit local participant is unavailable');
    await participant.setCameraEnabled(enabled);
  }

  Future<void> setMicrophoneEnabled(bool enabled) async {
    final room = _room;
    if (room == null) throw StateError('LiveKit room is not connected');
    final participant = room.localParticipant;
    if (participant == null)
      throw StateError('LiveKit local participant is unavailable');
    await participant.setMicrophoneEnabled(enabled);
  }

  Future<void> disconnect() async {
    final room = _room;
    _room = null;
    await room?.disconnect();
  }
}
