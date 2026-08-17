
class Recording {
  final String id, roomName, status, kind;
  final int? durationSeconds;
  final int? fileSizeBytes;
  Recording({required this.id, required this.roomName, required this.status, required this.kind, this.durationSeconds, this.fileSizeBytes});
  factory Recording.fromJson(Map<String,dynamic> j) => Recording(
    id:j['id'], roomName:j['room_name'], status:j['status'], kind:j['kind'],
    durationSeconds:j['duration_seconds'], fileSizeBytes:j['file_size_bytes']);
}
class TranscriptSegment {
  final int startMs,endMs,sequence; final String text;
  TranscriptSegment({required this.startMs,required this.endMs,required this.sequence,required this.text});
  factory TranscriptSegment.fromJson(Map<String,dynamic> j)=>TranscriptSegment(startMs:j['start_ms'],endMs:j['end_ms'],sequence:j['sequence'],text:j['text']);
}
class Transcript {
  final String id,text,provider; final String? language,model; final List<TranscriptSegment> segments;
  Transcript({required this.id,required this.text,required this.provider,this.language,this.model,required this.segments});
  factory Transcript.fromJson(Map<String,dynamic> j)=>Transcript(
    id:j['id'],text:j['text'],provider:j['provider'],language:j['language'],model:j['model'],
    segments:(j['segments'] as List).map((x)=>TranscriptSegment.fromJson(x)).toList());
}
class Report {
  final String id,summary; final double globalScore; final List strengths,weaknesses,recommendations; final Map competencyScores;
  Report({required this.id,required this.summary,required this.globalScore,required this.strengths,required this.weaknesses,required this.recommendations,required this.competencyScores});
  factory Report.fromJson(Map<String,dynamic> j)=>Report(id:j['id'],summary:j['summary'],globalScore:(j['global_score'] as num).toDouble(),strengths:j['strengths']??[],weaknesses:j['weaknesses']??[],recommendations:j['recommendations']??[],competencyScores:j['competency_scores']??{});
}
