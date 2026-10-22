import sys,json,hashlib,datetime,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(b):return hashlib.sha256(b).hexdigest()
trials=json.loads((ROOT/'experiment/trials.json').read_text())
command=sys.argv[1]
if command=='start':
 for number in map(int,sys.argv[2:]):
  t=trials[number-1]; d=ROOT/'work/capture'/t['trial_id'];d.mkdir(parents=True,exist_ok=False)
  (d/'dispatch.json').write_text(json.dumps({'ordinal':number,'trial_id':t['trial_id'],'dispatch_observed_utc':now()},indent=2)+'\n')
  print(number,t['trial_id']);print((ROOT/t['prompt_file']).read_text())
elif command=='record':
 number=int(sys.argv[2]);session=sys.argv[3];answer=sys.argv[4]
 t=trials[number-1]; d=ROOT/'records'/t['trial_id'];start=json.loads((ROOT/'work/capture'/t['trial_id']/'dispatch.json').read_text());d.mkdir(parents=True,exist_ok=False)
 with (d/'answer.txt').open('x') as f:f.write(answer)
 evidence={'trial_id':t['trial_id'],'session_id':session,'requested_model':'gpt-6.1-sol','requested_reasoning':'medium','fork_turns':'none','dispatch_observed_utc':start['dispatch_observed_utc'],'completion_observed_utc':now(),'backend':'collaboration.spawn_agent','observed_model':None,'tool_trace_available':False,'prompt_sha256':digest((ROOT/t['prompt_file']).read_bytes()),'response_sha256':digest((d/'answer.txt').read_bytes()),'capture_method':'coordinator copied returned final message'}
 with (d/'evidence.json').open('x') as f:f.write(json.dumps(evidence,indent=2)+'\n')
 print('Recorded',number,t['trial_id'])
elif command=='status':
 print('Answers',len(list((ROOT/'records').glob('*/answer.txt'))),'of',len(trials))
