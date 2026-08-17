
import 'media.dart';
class InterviewSummary {
 final String id,simulationId,status; final int currentQuestionIndex; final DateTime? startedAt,completedAt,expiresAt;
 InterviewSummary({required this.id,required this.simulationId,required this.status,required this.currentQuestionIndex,this.startedAt,this.completedAt,this.expiresAt});
 factory InterviewSummary.fromJson(Map<String,dynamic> j)=>InterviewSummary(id:j['id'],simulationId:j['simulation_id'],status:j['status'],currentQuestionIndex:j['current_question_index'],startedAt:j['started_at']==null?null:DateTime.parse(j['started_at']),completedAt:j['completed_at']==null?null:DateTime.parse(j['completed_at']),expiresAt:j['expires_at']==null?null:DateTime.parse(j['expires_at']));
}
class InterviewBundle { final InterviewSummary interview; final List<Recording> recordings; Report? report; Transcript? transcript; String? mediaUrl;
 InterviewBundle({required this.interview,required this.recordings,this.report,this.transcript,this.mediaUrl}); }
