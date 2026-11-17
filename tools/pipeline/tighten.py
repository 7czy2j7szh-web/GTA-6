import wave, sys, numpy as np
src, dst = sys.argv[1], sys.argv[2]
keep_gap = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
w=wave.open(src); sr=w.getframerate()
x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
win=int(0.01*sr); n=len(x)//win
e=np.sqrt((x[:n*win].reshape(n,win)**2).mean(1)); es=np.convolve(e,np.ones(3)/3,'same')
q=es<0.012
runs=[];i=0
while i<n:
    if q[i]:
        j=i
        while j<n and q[j]: j+=1
        if j-i>=12: runs.append((i*0.01,j*0.01))
        i=j
    else: i+=1
keep=[];prev=0;cuts=[]
for a,b in runs:
    if b-a>0.25 and a>0.05 and b<n*0.01-0.05:
        mid=(a+b)/2; cut=(b-a)-keep_gap
        keep.append((prev,int((mid-cut/2)*sr))); prev=int((mid+cut/2)*sr); cuts.append((round(a,2),round(b,2)))
keep.append((prev,len(x)))
parts=[]
for k,(s0,s1) in enumerate(keep):
    seg=x[s0:s1].copy(); f=int(0.004*sr)
    if k>0: seg[:f]*=np.linspace(0,1,f)
    if k<len(keep)-1: seg[-f:]*=np.linspace(1,0,f)
    parts.append(seg)
y=np.concatenate(parts)
o=wave.open(dst,'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((y*32767).astype(np.int16).tobytes()); o.close()
print('Pausen gekürzt:', len(cuts), 'Länge', round(len(x)/sr,2), '->', round(len(y)/sr,2))
