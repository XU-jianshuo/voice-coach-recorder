# Voice Coach Recorder

面向中文业务沟通场景的“公开录音 + 模型转写 + 说话人识别 + DeepSeek 沟通复盘”系统。

本项目不是普通录音机，而是个人沟通教练：

```text
安卓手机公开持续收音
→ 会话级切片与本地缓存
→ 腾讯云私有模型端转写
→ FunASR / SenseVoice 识别中文与说话人
→ DeepSeek 分析沟通表现
→ 形成谈话纪要、待办、话术改进和每日复盘
```

## 核心场景

- 客户拜访、渠道沟通、分公司督导、下属汇报。
- 识别“我”和不同外部说话人。
- 自动提取对方诉求、异议、承诺事项和后续动作。
- 分析本人表达是否清楚、是否压实责任、是否形成闭环。

## 技术路线

### Android 端

- Kotlin
- Jetpack Compose
- Foreground Service
- AudioRecord
- Room
- WorkManager
- OkHttp
- EncryptedSharedPreferences

Android 端只做稳定采集、会话级切片、本地缓存和结果展示，不做重模型推理。

### 腾讯云后端

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL 或 SQLite
- Redis + RQ/Celery
- Docker Compose
- FunASR / SenseVoice
- DeepSeek API

### 模型层优先级

1. FunASR / Paraformer / SenseVoice：中文 ASR、VAD、标点、热词、说话人分离。
2. sherpa-onnx：手机端或边缘端离线备用。
3. WhisperX / faster-whisper：对照基线或英文场景 fallback。

## 仓库规划

```text
voice-coach-recorder/
├── README.md
├── PROJECT_SPEC.md
├── CODEX_TASKS.md
├── .env.example
├── docs/
│   ├── architecture.md
│   ├── api-contract.md
│   ├── tencent-cloud-deploy.md
│   └── deepseek-prompts.md
├── backend/
│   ├── app/
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
└── android/
    └── VoiceCoachRecorder/
```

## Codex 开工建议

第一条指令建议：

```text
Read PROJECT_SPEC.md and CODEX_TASKS.md. Start with Milestone 1 only. Implement the backend skeleton with FastAPI, SQLAlchemy models, upload endpoint, health check, environment config, and Docker Compose. Do not implement Android or ASR yet.
```

每次只让 Codex 完成一个里程碑，避免项目写散。

## 合规原则

- 只做公开录音，通知栏常驻显示录音状态。
- 不做隐藏录音、无提示录音或规避系统限制。
- 默认音频本地加密保存。
- 默认上传到用户自己的腾讯云服务器。
- 支持一键暂停、私人场景过滤、自动删除无效音频。
