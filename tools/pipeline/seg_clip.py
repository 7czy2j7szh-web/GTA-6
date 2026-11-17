import sys, os, time, cv2
from PIL import Image
import onnxruntime as ort
from rembg import remove, new_session
src, out, model = sys.argv[1], sys.argv[2], sys.argv[3]
so = ort.SessionOptions(); so.enable_cpu_mem_arena = False; so.intra_op_num_threads = 3; so.inter_op_num_threads = 1
s = new_session(model, sess_opts=so)
cap = cv2.VideoCapture(src); n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); i = -1; t0 = time.time()
while True:
    ok, f = cap.read()
    if not ok: break
    i += 1
    p = f"{out}/{i:04d}.png"
    if os.path.exists(p): continue
    m = remove(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)), session=s, only_mask=True)
    m.save(p)
    if i % 10 == 0:
        el = time.time() - t0
        print(f"{i}/{n} {el/ max(i,1):.1f}s/Bild", flush=True)
print("fertig", i + 1)
