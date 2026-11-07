"""Builds data/benchmarks.csv and data/boards.csv from sources collected 2026-10-17.
Every number below was transcribed from the cited public source. Nothing is estimated or derived."""
import csv, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'raw')
rows = []
def add(platform, board, accelerator, runtime, model, params_b, quant, gen, src_name, url, date, date_type,
        src_type, prompt=None, ttft=None, model_type='llm', notes=''):
    rows.append(dict(platform=platform, board=board, accelerator=accelerator, runtime=runtime, model=model,
        params_b=params_b, quant=quant, gen_tps=gen, prompt_tps=prompt if prompt is not None else '',
        ttft_ms=ttft if ttft is not None else '', model_type=model_type, source_name=src_name, source_url=url,
        source_date=date, date_type=date_type, source_type=src_type, notes=notes))

# ---------- 1. Rockchip RKLLM official benchmark.md (commit f739053, 2026-09-29) ----------
RK_URL = 'https://github.com/airockchip/rknn-llm/blob/f7390530443bf84f0394255a449d7cbe81e69d1c/benchmark.md'
NAMEFIX = {'Qwen2':'Qwen2','MiniCPM4':'MiniCPM4','Qwen3':'Qwen3','TinyLLAMA':'TinyLlama','Qwen2.5':'Qwen2.5','RWKV7':'RWKV7',
  'InternLM2':'InternLM2','Gemma2':'Gemma 2','Gemma3n':'Gemma 3n','Gemma-3n':'Gemma 3n','TeleChat2':'TeleChat2','Phi3':'Phi-3',
  'MiniCPM3':'MiniCPM3','ChatGLM3':'ChatGLM3','Qwen3-VL':'Qwen3-VL','DeepSeekOCR':'DeepSeek-OCR','Qwen3.5':'Qwen3.5',
  'Gemma4':'Gemma 4','LFM2.5-VL':'LFM2.5-VL','Spark-X2.5':'Spark-X2.5'}
txt = open(os.path.join(RAW,'rkllm_main.md')).read()
for chip in ['RK3588','RK3576']:
    sec = txt.split('### '+chip)[1].split('###')[0]
    last = None
    for line in sec.splitlines():
        c = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(c) != 8 or c[0].startswith(':') or c[0]=='Model': continue
        name = c[0] or last; last = name
        size = c[1]
        nm = NAMEFIX.get(name, name)
        mtype = 'vlm' if ('VL' in name or 'OCR' in name) else 'llm'
        add(chip.lower(), f'Rockchip {chip} (vendor reference board)', f'{chip} NPU', 'RKLLM v1.3.1',
            f'{nm} {size}', re.sub(r'[^0-9.]','',size.split('(')[0]) if 'E' not in size else '', c[2],
            float(c[6]), 'Rockchip rknn-llm benchmark.md', RK_URL, '2026-09-29', 'commit', 'vendor',
            ttft=float(c[5]), model_type=mtype,
            notes=f'seqlen {c[3]}, {c[4]} new tokens; max CPU/NPU freq; memory {c[7]} MB')

# ---------- 2. NVIDIA JetPack 6.2 Super Mode blog (2025-01-16), MLC INT4 ----------
NV_URL = 'https://developer.nvidia.com/blog/nvidia-jetpack-6-2-brings-super-mode-to-nvidia-jetson-orin-nano-and-jetson-orin-nx-modules/'
nv = {
 'jetson-orin-nano': ('Jetson Orin Nano 8GB (original mode)', [14.00,27.70,14.20,21.5,7.20,24.70,41.00]),
 'jetson-orin-nano-super': ('Jetson Orin Nano 8GB (Super mode)', [19.10,43.10,21.80,35.0,9.20,38.10,64.50]),
 'jetson-orin-nx-8gb': ('Jetson Orin NX 8GB (original mode)', [15.90,34.50,17.10,26.60,8.80,30.80,51.50]),
 'jetson-orin-nx-8gb-super': ('Jetson Orin NX 8GB (Super mode)', [23.10,46.50,23.80,39.30,13.38,41.30,69.80]),
 'jetson-orin-nx-16gb': ('Jetson Orin NX 16GB (original mode)', [20.50,40.40,20.80,31.60,10.56,35.90,59.50]),
 'jetson-orin-nx-16gb-super': ('Jetson Orin NX 16GB (Super mode)', [22.80,45.80,23.50,39.00,13.26,40.90,68.80]),
}
nvm = [('Llama 3.1 8B','8'),('Llama 3.2 3B','3'),('Qwen2.5 7B','7'),('Gemma 2 2B','2'),('Gemma 2 9B','9'),('Phi-3.5 3.8B','3.8'),('SmolLM2 1.7B','1.7')]
for plat,(board,vals) in nv.items():
    for (m,p),v in zip(nvm,vals):
        add(plat, board, 'Ampere GPU', 'MLC', m, p, 'INT4', v, 'NVIDIA Technical Blog (JetPack 6.2 Super Mode)', NV_URL,
            '2025-01-16', 'published', 'vendor', notes='Tables 4-6; generation tokens/s, INT4 via MLC API')

# ---------- 3. Jetson AI Lab SLM tutorial (archive page) ----------
JAL = 'https://www.jetson-ai-lab.com/archive/tutorial_slm.html'
add('jetson-orin-nano','Jetson Orin Nano','Ampere GPU','MLC 0.1.2 (dustynv/mlc:0.1.2-r36.3.0)','Llama 3.2 1B','1','INT4',54.8,'NVIDIA Jetson AI Lab: Small LLM tutorial',JAL,'2026-10-17','accessed','vendor')
add('jetson-agx-orin','Jetson AGX Orin','Ampere GPU','MLC 0.1.2 (dustynv/mlc:0.1.2-r36.3.0)','Llama 3.2 1B','1','INT4',163.9,'NVIDIA Jetson AI Lab: Small LLM tutorial',JAL,'2026-10-17','accessed','vendor')
add('jetson-agx-orin','Jetson AGX Orin','Ampere GPU','MLC 0.1.2 (dustynv/mlc:0.1.2-r36.3.0)','Llama 3.2 3B','3','INT4',80.4,'NVIDIA Jetson AI Lab: Small LLM tutorial',JAL,'2026-10-17','accessed','vendor')

# ---------- 4. arXiv 2604.24785 Cloud to Edge (2026-04-24), Ollama variants + StackFlow ----------
AX = 'https://arxiv.org/abs/2604.24785'
cols = [('m5stack-module-llm','M5Stack Module LLM (AX630C)','AX630C NPU','StackFlow'),
        ('rpi5','Raspberry Pi 5 8GB','CPU (Cortex-A76)','Ollama'),
        ('rpi5-ai-hat-plus-2','Raspberry Pi 5 + AI HAT+ 2','Hailo-10H NPU','hailo-ollama'),
        ('jetson-orin-nano-super','Jetson Orin Nano Super Dev Kit (CPU only)','CPU (Cortex-A78AE)','Ollama'),
        ('jetson-orin-nano-super','Jetson Orin Nano Super Dev Kit','Ampere GPU','Ollama')]
ax = [('DeepSeek-R1-Distill-Qwen 1.5B','1.5',[2.42,0.32,1.53,6.01,9.59]),
      ('Qwen2.5 0.5B','0.5',[None,0.86,None,13.04,13.31]),
      ('Qwen2.5 1.5B','1.5',[None,0.27,4.37,4.21,9.37]),
      ('Qwen2.5 1.5B Instruct','1.5',[2.55,0.3,6.34,6.9,9.09]),
      ('Qwen2.5-Coder 1.5B','1.5',[None,0.3,2.07,6.76,8.66]),
      ('Llama 3.2 1B','1',[3.44,0.39,None,9.51,10.96]),
      ('Llama 3.2 3B','3',[None,0.14,1.01,4.3,6.31])]
for m,p,vals in ax:
    for (plat,board,acc,rt),v in zip(cols,vals):
        if v is None: continue
        add(plat,board,acc,rt,m,p,'not reported',v,'arXiv 2604.24785 (Cloud to Edge)',AX,'2026-04-24','published','academic',
            notes='Table: throughput tok/s. Runtime per paper: Ollama variants + StackFlow (M5Stack). TTFT omitted (units ambiguous in source).')

# ---------- 5. CNX Software AI HAT+ 2 review (2026-01-20), Ollama / hailo-ollama ----------
CNX = 'https://www.cnx-software.com/2026/01/20/raspberry-pi-ai-hat-2-review-a-40-tops-ai-accelerator-tested-with-computer-vision-llm-and-vlm-workloads/'
for m,p,cpu,hat in [('DeepSeek-R1-Distill-Qwen 1.5B','1.5',9.04,6.72),('Qwen2 1.5B','1.5',11.29,5.89),('Llama 3.2 3B','3',4.78,2.60),
                    ('Qwen2.5 1.5B Instruct','1.5',11.73,6.74),('Qwen2.5-Coder 1.5B','1.5',10.26,8.06)]:
    add('rpi5','Raspberry Pi 5 / CM5','CPU (Cortex-A76)','Ollama',m,p,'Ollama default',cpu,'CNX Software: AI HAT+ 2 review',CNX,'2026-01-20','published','independent')
    add('rpi5-ai-hat-plus-2','Raspberry Pi 5 + AI HAT+ 2','Hailo-10H NPU','hailo-ollama',m,p,'Hailo-compiled',hat,'CNX Software: AI HAT+ 2 review',CNX,'2026-01-20','published','independent')

# ---------- 6. schwab.sh AI HAT+ 2 benchmarks (test date 2026-01-25) ----------
SW = 'https://www.schwab.sh/blog/hailo-ai-hat-benchmarks/'
for m,p,v in [('Qwen2 1.5B','1.5',8.03),('Qwen2.5-Coder 1.5B','1.5',7.94),('DeepSeek-R1-Distill-Qwen 1.5B','1.5',6.83),('Qwen2.5 1.5B Instruct','1.5',6.76),('Llama 3.2 3B','3',2.65)]:
    add('rpi5-ai-hat-plus-2','Raspberry Pi 5 8GB + AI HAT+ 2','Hailo-10H NPU','hailo-ollama',m,p,'Hailo-compiled',v,'schwab.sh: Benchmarking the AI HAT+ 2',SW,'2026-01-25','tested','independent',notes='15 minutes per model')

# ---------- 7. Edge-LLM-Bench (ACM) - only per-model numbers stated in text ----------
ACM = 'https://dl.acm.org/doi/10.1145/3812836.3814998'
add('rpi5-ai-hat-plus-2','Raspberry Pi 5 + Hailo-10H','Hailo-10H NPU','hailo-ollama','Llama 3.2 1B','1','Hailo-compiled',8.7,'Edge-LLM-Bench (ACM)',ACM,'2026','published (year only)','academic',notes='±1.1 tok/s; n=90')
add('rpi5','Raspberry Pi 5','CPU (Cortex-A76)','CPU backend (per paper)','Llama 3.2 1B','1','not reported',8.4,'Edge-LLM-Bench (ACM)',ACM,'2026','published (year only)','academic',ttft=985)
add('rpi5','Raspberry Pi 5','CPU (Cortex-A76)','CPU backend (per paper)','Qwen3 1.7B','1.7','not reported',7.8,'Edge-LLM-Bench (ACM)',ACM,'2026','published (year only)','academic',ttft=1653)

# ---------- 8. Jeff Geerling ai-benchmarks issue #7 (2025-01-09), Ollama, no tweaks ----------
JG = 'https://github.com/geerlingguy/ai-benchmarks/issues/7'
for b,m,p,v in [('Raspberry Pi 5 16GB','Llama 3.2 3B','3',4.51),('Raspberry Pi 5 16GB','Llama 3.1 8B','8',2.05),('Raspberry Pi 5 16GB','Llama 2 13B','13',1.35),
                ('Raspberry Pi 5 8GB','Llama 3.2 3B','3',4.61),('Raspberry Pi 5 8GB','Llama 3.1 8B','8',1.99)]:
    add('rpi5',b,'CPU (Cortex-A76)','Ollama',m,p,'Ollama default',v,'Jeff Geerling: ai-benchmarks #7',JG,'2025-01-09','published','independent',notes='Test 2 (no NUMA tweaks) / 8GB comparison table')

# ---------- 9. RPubs: LLM performance on Raspberry Pi 5 (Ollama, Q4_K_M) ----------
RP = 'https://rstudio-pubs-static.s3.amazonaws.com/1315005_1e9af5bd949b42d8ab2345e2786ec71e.html'
for m,p,q,v in [('Qwen2.5 3B','3','Q4_K_M',5.2),('Llama 3.2 1B Instruct','1','Q4_K_M',11.22),('SmolLM2 1.7B Instruct','1.7','Q4_K_M',8.23),
                ('Granite 3.1 Dense 2B','2','Q4_K_M',5.81),('Llama 3.2 3B','3','Q4_K_M',4.69),('Qwen2.5 1.5B','1.5','Q4_K_M',9.97),
                ('Gemma 3 1B','1','Q4_K_M',11.53),('BitNet b1.58 2B-4T','2','Q1.5',8.13)]:
    add('rpi5','Raspberry Pi 5','CPU (Cortex-A76)','Ollama',m,p,q,v,'RPubs: Analysis of LLM performance on the Raspberry Pi 5',RP,'2026-10-17','accessed','community',notes='simple prompt; no publish date shown')

# ---------- 10. distributed-llama discussion #165 (2025-02-15) ----------
DL = 'https://github.com/b4rtaz/distributed-llama/discussions/165'
for plat,b,pr,g in [('rpi5','1x Raspberry Pi 5 8GB',14.30,5.95),('rpi5-cluster','2x Raspberry Pi 5 8GB',23.63,10.33),('rpi5-cluster','4x Raspberry Pi 5 8GB',27.74,13.68)]:
    add(plat,b,'CPU (Cortex-A76)','distributed-llama v0.12.3','Llama 3.2 3B Instruct','3','Q40',g,'distributed-llama discussion #165',DL,'2025-02-15','published','community',prompt=pr,notes='Evaluation = prompt tok/s, Prediction = generation tok/s')

# ---------- 11. Indiedroid Nova (RK3588S) RKLLM - TrevTron repo (2026-01-12) + ameriDroid ODROID-M2 ----------
NOVA = 'https://github.com/TrevTron/indiedroid-nova-llm'
for m,p,v in [('Llama 3.1 8B Instruct','8',3.72),('Qwen2.5 3B Instruct','3',7.0),('DeepSeek-R1-Distill-Qwen 1.5B','1.5',11.5)]:
    add('rk3588','Indiedroid Nova (RK3588S, 16GB)','RK3588S NPU','RKLLM runtime 1.2.1',m,p,'w8a8 (RKLLM conversion)' if m.startswith('Llama') else 'RKLLM conversion',v,'TrevTron/indiedroid-nova-llm (also posted to r/LocalLLaMA)',NOVA,'2026-01-12','repo created','community',notes='Hardware provided by ameriDroid; r/LocalLLaMA post: https://www.reddit.com/r/LocalLLaMA/comments/1qjb4m0/')
add('rk3588','ODROID-M2 (RK3588S2, 16GB)','RK3588 NPU','RKLLM','Qwen2.5 3B Instruct','3','RKLLM conversion',8.45,'ameriDroid blog','https://ameridroid.com/blogs/ameriblogs/rk3588-npu-shines-for-local-llms-indiedroid-nova-and-odroid-m2-performance-comparison','2026-01-21','published','vendor',notes='"~8.45 tokens/second sustained on long generations"; retailer test')

# ---------- 12. raspberry.tips Arduino UNO Q (2026-08-21) ----------
add('arduino-uno-q','Arduino UNO Q (4GB)','CPU (NPU unused)','llama.cpp (App Lab)','Gemma 3 1B','1','not reported',5.5,'raspberry.tips: Can the Arduino UNO Q run an LLM?','https://raspberry.tips/en/arduino/arduino-uno-q-local-ai-chatbot','2026-08-21','published','independent',prompt=9.7,notes='~ values as reported; ~1.4 W under load')

# ---------- 13. M5Stack StackFlow benchmark page ----------
M5 = 'https://docs.m5stack.com/en/stackflow/models/benchmark'
m5map = {'Module LLM Kit / LLM630 Compute Kit':('m5stack-module-llm','M5Stack Module LLM / LLM630 (AX630C)','AX630C NPU','StackFlow'),
         'LLM8850':('m5stack-llm8850','M5Stack LLM8850 M.2 card (AX8850)','AX8850 NPU','StackFlow'),
         'AI Pyramid':('m5stack-ai-pyramid','M5Stack AI Pyramid (AX8850)','AX8850 NPU','StackFlow'),
         'Hailo-10H':('rpi5-ai-hat-plus-2','Hailo-10H (host not stated)','Hailo-10H NPU','per M5Stack page'),
         'RaspberryPi5 CPU (ollama)':('rpi5','Raspberry Pi 5','CPU (Cortex-A76)','Ollama')}
m5 = [('DeepSeek-R1-Distill-Qwen 1.5B','1.5',128,'W8A16',1075.04,3.57,'Module LLM Kit / LLM630 Compute Kit'),
 ('DeepSeek-R1-Distill-Qwen 1.5B','1.5',256,'W4A16',None,13.29,'LLM8850'),
 ('DeepSeek-R1-Distill-Qwen 1.5B','1.5',None,'W4A8',660,7.05,'Hailo-10H'),
 ('Llama 3.2 1B Instruct','1',128,'W8A16',891,4.48,'Module LLM Kit / LLM630 Compute Kit'),
 ('MiniCPM4 0.5B','0.5',512,'W8A16',212.91,21.05,'LLM8850'),
 ('Qwen2.5 0.5B Instruct','0.5',128,'W8A16',359.8,10.32,'Module LLM Kit / LLM630 Compute Kit'),
 ('Qwen2.5 0.5B Instruct','0.5',128,'W4A16',442.95,12.52,'Module LLM Kit / LLM630 Compute Kit'),
 ('Qwen2.5 0.5B Instruct','0.5',128,'W4A16',140.17,37.11,'AI Pyramid'),
 ('Qwen2.5 0.5B Instruct','0.5',128,'W4A16',None,27.05,'LLM8850'),
 ('Qwen2.5 1.5B Instruct','1.5',128,'W8A16',3056.54,3.57,'Module LLM Kit / LLM630 Compute Kit'),
 ('Qwen2.5 1.5B Instruct','1.5',128,'W4A16',1219.54,4.63,'Module LLM Kit / LLM630 Compute Kit'),
 ('Qwen2.5 1.5B Instruct','1.5',128,'W4A16',289.06,16.77,'AI Pyramid'),
 ('Qwen2.5 1.5B Instruct','1.5',128,'W4A16',None,15.06,'LLM8850'),
 ('Qwen2.5 1.5B Instruct','1.5',None,'W4A8',370,6.82,'Hailo-10H'),
 ('Qwen2.5 3B Instruct','3',128,'W4A16',550.3,9.46,'AI Pyramid'),
 ('Qwen2.5 0.5B Instruct','0.5',1024,'W8A16',143.02,25.5,'AI Pyramid'),
 ('Qwen2.5 0.5B Instruct','0.5',None,'not reported',8210,1.54,'RaspberryPi5 CPU (ollama)'),
 ('Qwen3 0.6B','0.6',128,'W8A16',361.81,10.28,'Module LLM Kit / LLM630 Compute Kit'),
 ('Qwen3 0.6B','0.6',2048,'W8A16',670.51,12.88,'LLM8850'),
 ('Qwen3 1.7B','1.7',2048,'W8A16',796.38,7.38,'LLM8850'),
 ('InternVL3 1B','1',1024,'W8A16',534.95,9.78,'Module LLM Kit / LLM630 Compute Kit'),
 ('InternVL3 1B','1',2048,'W8A16',142.32,26.67,'AI Pyramid'),
 ('Qwen3-VL 2B Instruct','2',1152,'W8A16',159.79,11.93,'AI Pyramid'),
 ('Qwen3-VL 2B Instruct','2',1152,'W8A16',None,7.8,'LLM8850'),
 ('Qwen3-VL 2B Instruct','2',None,'not reported',24909,0.42,'RaspberryPi5 CPU (ollama)')]
for m,p,ctx,q,tt,g,dev in m5:
    plat,b,acc,rt = m5map[dev]
    add(plat,b,acc,rt,m,p,q,g,'M5Stack docs: Model Performance Benchmarks',M5,'2026-10-17','accessed','vendor',ttft=tt,
        model_type='vlm' if 'VL' in m else 'llm', notes=(f'context {ctx}' if ctx else '')+('; vendor-published comparison' if dev in ('Hailo-10H','RaspberryPi5 CPU (ollama)') else ''))

# ---------- 14. SimpleDirect: Piccolo on Jetson and Raspberry Pi (2026-10-05) ----------
SD = 'https://www.getsimpledirect.com/blog/piccolo-jetson-raspberry-pi'
for prof,j,pi in [('Thinking general',13.98,2.95),('Thinking precise coding',14.77,3.21),('Instruct general',13.41,3.19),('Instruct reasoning',13.19,3.00)]:
    add('jetson-orin-nano','Jetson Orin Nano (~7.4 GiB usable)','Ampere GPU (CUDA)','llama.cpp','Vinci Piccolo 1.0 (Qwen3.5-4B based)','4','Q4_K_M',j,'SimpleDirect: Piccolo on Jetson and Raspberry Pi',SD,'2026-10-05','published','vendor',notes=f'prompt profile: {prof}; single run; power mode not stated')
    add('rpi5','Raspberry Pi 5 (~15 GiB usable)','CPU (Cortex-A76)','llama.cpp','Vinci Piccolo 1.0 (Qwen3.5-4B based)','4','Q4_K_M',pi,'SimpleDirect: Piccolo on Jetson and Raspberry Pi',SD,'2026-10-05','published','vendor',notes=f'prompt profile: {prof}; single run')

# ---------- 15. X post: Jetson Orin Nano vs Thor (2026-08-25) ----------
XU = 'https://x.com/michellelsun/status/2092338690869895288'
for m,p,n,t in [('Qwen3.5 4B','4',18,68),('Gemma 4 E2B','',34,133),('Gemma 4 E4B','',17,95),('Qwen3.5 9B','9',12,73)]:
    add('jetson-orin-nano','Jetson Orin Nano (post says "Orin Nano 2")','Ampere GPU','not stated',m,p,'not stated',n,'X post by @michellelsun',XU,'2026-08-25','published','community',notes='runtime/quant not stated in post text')
    add('jetson-agx-thor','Jetson AGX Thor','Blackwell GPU','not stated',m,p,'not stated',t,'X post by @michellelsun',XU,'2026-08-25','published','community',notes='runtime/quant not stated in post text')

# ---------- 16. NVIDIA research: Nemotron 3.5 Bolt E4B 4GB (2026-10-23) ----------
NB = 'https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Bolt-E4B-4GB/'
for plat,b,g,tt,cfg,vram in [('jetson-orin-nano','Jetson Orin Nano 8GB (power mode not stated)',15.5,5785,'0 cached / 3K input / 50 output',4.2),
                         ('jetson-orin-nano','Jetson Orin Nano 8GB (power mode not stated)',13.0,6259,'32K cached / 2K input / 256 output',4.9),
                         ('jetson-agx-orin','Jetson AGX Orin 32GB',24.0,3687,'0 cached / 3K input / 50 output',4.2),
                         ('jetson-agx-orin','Jetson AGX Orin 32GB',20.3,4091,'32K cached / 2K input / 256 output',5.0)]:
    add(plat,b,'Ampere GPU (CUDA)','llama.cpp (CUDA), AIPerf','Nemotron 3.5 Bolt E4B','','Q4_K_M',g,'NVIDIA Research: Nemotron 3.5 Bolt E4B 4GB',NB,'2026-10-23','published','vendor',ttft=tt,
        notes=f'{cfg}; batch 1; VRAM {vram} GB; 8B total / 4B effective params (built on Gemma 4 E4B)')

# ---------- 17. X post: Gemma 4 E2B on 8GB Orin Nano, TensorRT Edge-LLM (2026-10-22) ----------
MC = 'https://x.com/mihaichiorean/status/2113355664236163321'
add('jetson-orin-nano-super','Jetson Orin Nano 8GB (25 W per author)','Ampere GPU','TensorRT Edge-LLM 0.11 (author-tuned)','Gemma 4 E2B','','AWQ INT4 (INT8 embedding tables)',42.7,'X post by @mihaichiorean',MC,'2026-10-22','published','community',ttft=199,
    notes='TTFT on an 846-token prompt (stock recipe 485 ms); runtime/quant/power from author reply https://x.com/mihaichiorean/status/2113767627097346246')

# ---------- 18. Seeed Studio wiki: MTP speculative decoding on AGX Orin 32GB (2026-10-23) ----------
SMTP = 'https://wiki.seeedstudio.com/jetson/accelerate_llm_inference_mtp/'
for g,rt,nt in [(25.6,'llama.cpp (CUDA), llama-server, MTP off','MTP off baseline'),
                (49.7,'llama.cpp (CUDA), llama-server, MTP speculative decoding','MTP on; gain depends on the task (measured on deterministic code output)')]:
    add('jetson-agx-orin','Jetson AGX Orin 32GB (JetPack 6.2.1)','Ampere GPU (CUDA)',rt,'Qwen3.5 4B','4','Q4_K_M (MTP-enabled GGUF)',g,'Seeed Studio wiki (zibo)',SMTP,'2026-10-23','updated','vendor',
        notes=f'{nt}; generating a Python Fibonacci script; same device and model')

# ---------- 19. NVIDIA Jetson AI Lab: speculative decoding tutorial, AGX Thor (2026-10) ----------
JSD = 'https://www.jetson-ai-lab.com/tutorials/speculative-decoding/'
for g,rt,nt in [(13,'llama.cpp (CUDA), no speculative decoding','approximate ("roughly 13 tokens/s"); baseline'),
                (35,'llama.cpp (CUDA), MTP speculative decoding depth 3','approximate ("35 tokens/s"); MTP depth 3')]:
    add('jetson-agx-thor','Jetson AGX Thor','Blackwell GPU',rt,'Qwen3.8 27B','27','not stated',g,'NVIDIA Jetson AI Lab tutorial',JSD,'2026-10','published','vendor',
        notes=f'{nt}; prompt length and power mode not stated')

# model slug
def mslug(m):
    s = m.lower()
    s = re.sub(r'\(.*?\)','',s)
    s = s.replace('instruct','').replace('dense','')
    return re.sub(r'[^a-z0-9.]+','-',s).strip('-').replace('.-','-')
for i,r in enumerate(rows,1):
    r['id'] = f'b{i:04d}'; r['model_slug'] = mslug(r['model'])
fields = ['id','platform','board','accelerator','runtime','model','model_slug','model_type','params_b','quant','gen_tps','prompt_tps','ttft_ms','source_name','source_url','source_date','date_type','source_type','notes']
with open(os.path.join(ROOT,'data','benchmarks.csv'),'w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

# ---------- boards.csv ----------
CNXP = 'https://www.cnx-software.com/2026/04/01/raspberry-pi-4-3gb-launched-for-83-75-further-price-increases-announced-across-the-board-for-4gb-ram-hardware/'
HWB = 'https://hwbusters.com/news/nvidia-jetson-prices-jump-up-to-101-the-249-orin-nano-super-is-now-399/'
AMD = 'https://ameridroid.com/collections/single-board-computer'
SBC = 'https://sbc.compare/radxa'
boards = [
 # platform, name, chip, memory, price, currency, note, url, date
 ('rpi5','Raspberry Pi 5 8GB','Broadcom BCM2712','8GB LPDDR4X',175,'USD','official list price after Apr 2026 increase',CNXP,'2026-04-01'),
 ('rpi5','Raspberry Pi 5 16GB','Broadcom BCM2712','16GB LPDDR4X',305,'USD','official list price after Apr 2026 increase',CNXP,'2026-04-01'),
 ('rpi5-ai-hat-plus-2','Raspberry Pi AI HAT+ 2 (add-on, needs a Pi 5)','Hailo-10H','8GB on HAT',180,'USD','official list price after Apr 2026 increase (launched at $130)',CNXP,'2026-04-01'),
 ('rpi5-ai-hat-plus-2','Raspberry Pi 5 + AI HAT+ 2 (as tested in paper)','BCM2712 + Hailo-10H','8GB + 8GB',451.83,'USD','price quoted in arXiv paper',AX,'2026-04-24'),
 ('rpi5-cluster','Raspberry Pi 5 8GB (per node)','Broadcom BCM2712','8GB LPDDR4X',175,'USD','multiply by node count',CNXP,'2026-04-01'),
 ('jetson-orin-nano-super','Jetson Orin Nano Super Developer Kit','Orin (Ampere GPU)','8GB LPDDR5',399,'USD','raised from $249 (July 2026 report)',HWB,'2026-07-21'),
 ('jetson-orin-nano','Jetson Orin Nano Developer Kit (same hardware, original power mode)','Orin (Ampere GPU)','8GB LPDDR5',399,'USD','same dev kit as Super; Super mode is a JetPack 6.2 flash',HWB,'2026-07-21'),
 ('jetson-agx-orin','Jetson AGX Orin Developer Kit','Orin (Ampere GPU)','64GB',3499,'USD','raised from $1,999',HWB,'2026-07-21'),
 ('jetson-agx-thor','Jetson AGX Thor Developer Kit','Thor (Blackwell GPU)','128GB',5499,'USD','raised from $3,499',HWB,'2026-07-21'),
 ('rk3588','Radxa ROCK 5B 8GB','RK3588','8GB',160,'USD','listed price',SBC,'2026-10-17'),
 ('rk3588','Radxa ROCK 5B+ 16GB','RK3588','16GB',135,'USD','listed price',SBC,'2026-10-17'),
 ('rk3588','Indiedroid Nova + heatsink, fan, eMMC','RK3588S','16GB',199.95,'USD','sale price',AMD,'2026-10-17'),
 ('rk3588','ODROID-M2 w/ case, 64GB eMMC','RK3588S2','from 8GB',299.95,'USD','"from" price',AMD,'2026-10-17'),
 ('rk3576','Radxa ROCK 4D 8GB','RK3576','8GB',106,'USD','listed price',SBC,'2026-10-17'),
 ('m5stack-module-llm','M5Stack LLM Module Kit (AX630C)','AX630C','4GB',79.90,'USD','regular price; out of stock when checked','https://shop.m5stack.com/products/m5stack-llm-large-language-model-module-kit-ax630c','2026-10-17'),
 ('m5stack-module-llm','M5Stack Module LLM (as tested in paper)','AX630C','4GB',99.90,'USD','price quoted in arXiv paper',AX,'2026-04-24'),
 ('m5stack-ai-pyramid','M5Stack AI Pyramid (AX8850)','AX8850','',None,'USD','price not verified','',''),
 ('m5stack-llm8850','M5Stack LLM8850 M.2 card (AX8850)','AX8850','',None,'USD','price not verified','',''),
 ('jetson-orin-nx-8gb','Jetson Orin NX 8GB module','Orin (Ampere GPU)','8GB',None,'USD','price not verified','',''),
 ('jetson-orin-nx-8gb-super','Jetson Orin NX 8GB module (Super mode)','Orin (Ampere GPU)','8GB',None,'USD','price not verified','',''),
 ('jetson-orin-nx-16gb','Jetson Orin NX 16GB module','Orin (Ampere GPU)','16GB',None,'USD','price not verified','',''),
 ('jetson-orin-nx-16gb-super','Jetson Orin NX 16GB module (Super mode)','Orin (Ampere GPU)','16GB',None,'USD','price not verified','',''),
 ('arduino-uno-q','Arduino UNO Q 4GB','Qualcomm QRB2210','4GB',None,'USD','price not verified','',''),
]
with open(os.path.join(ROOT,'data','boards.csv'),'w',newline='') as f:
    w = csv.writer(f); w.writerow(['platform','board_name','chip','memory','price','currency','price_note','price_source_url','price_date'])
    for b in boards: w.writerow(['' if x is None else x for x in b])
print(len(rows),'benchmark rows;',len(boards),'board rows')
