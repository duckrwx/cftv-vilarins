# Execucao local do MVP

Este documento registra o fluxo local da versao Bitcoin/OpenTimestamps.

## Dependencias

```text
pip install opentimestamps-client
```

Tambem sao necessarios `ffmpeg`, `ffprobe` e `openssl`.

## 1. Segmentar video

```text
python3 src/segmenter/segment_video.py \
  --input data/input/video.mp4 \
  --output-dir data/segments \
  --segment-seconds 2 \
  --metadata data/segments/segments_metadata.json \
  --mode reencode
```

## 2. Gerar pacote SIP BagIt

```text
python3 src/packager/create_package.py \
  --segments-dir data/segments \
  --output-dir data/packages \
  --package-id camera-001-20260615T210000Z \
  --segment-seconds 2 \
  --source-duration-seconds 7.7
```

## 3. Validar pacote no gateway

```text
python3 src/gateway/validate_package.py \
  --package data/packages/camera-001-20260615T210000Z \
  --public-key keys/device_public.pem \
  --report reports/gateway_validation_report.json
```

Resultado esperado:

```text
status: COMPLETE
bagit_valid: true
signature_valid: true
sequence_valid: true
```

## 4. Gerar prova OpenTimestamps

```text
python3 src/anchor/stamp_manifest.py \
  --package data/packages/camera-001-20260615T210000Z \
  --report reports/ots_stamp_report.json
```

Prova gerada:

```text
data/packages/camera-001-20260615T210000Z/timestamp/hour_manifest.json.ots
```

A prova pode ficar pendente ate a confirmacao da ancora em Bitcoin. Para tentar atualizar:

```text
ots upgrade data/packages/camera-001-20260615T210000Z/timestamp/hour_manifest.json.ots
```

## 5. Verificar pacote integro

```text
python3 src/verifier/verify_package.py \
  --package data/packages/camera-001-20260615T210000Z \
  --public-key keys/device_public.pem \
  --report reports/integrity_report.json
```

Resultado esperado:

```text
status: INTEGRO
```

Logo apos o stamp, o resultado tambem pode ser:

```text
status: PENDENTE_BITCOIN
```

Nesse caso a cadeia local esta integra, mas a prova OpenTimestamps ainda aguarda confirmacao em Bitcoin. Para aceitar esse estado na demo:

```text
python3 src/verifier/verify_package.py --allow-pending
```

Antes de gerar `.ots`, use somente para teste local:

```text
python3 src/verifier/verify_package.py --skip-ots
```

## 6. Verificar pacote adulterado

```text
bash scripts/make_tampered_cases.sh
python3 src/verifier/verify_package.py \
  --package data/tampered/case-01-segment-bytes-modified \
  --public-key keys/device_public.pem \
  --skip-ots \
  --report reports/tampered_report.json
```

Resultado esperado:

```text
status: INVALIDO
```

## Estado esperado

O MVP demonstra:

- segmentacao de video;
- geracao de hashes;
- manifesto com encadeamento;
- assinatura do manifesto;
- pacote BagIt minimo;
- validacao por gateway;
- timestamp OpenTimestamps;
- verificacao independente;
- deteccao de adulteracao.
