import base64, json, subprocess, sys
wav, prompt, out = sys.argv[1], sys.argv[2], sys.argv[3]
b=base64.b64encode(open(wav,'rb').read()).decode()
body={"contents":[{"parts":[{"inlineData":{"mimeType":"audio/wav","data":b}},{"text":prompt}]}]}
open(out,'w').write(json.dumps(body))
r=subprocess.run(['curl','-sS','-m','240','-H','Content-Type: application/json','-d','@'+out,'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent'],capture_output=True,text=True)
d=json.loads(r.stdout)
try: print(d['candidates'][0]['content']['parts'][0]['text'])
except Exception: print(r.stdout[:600])
