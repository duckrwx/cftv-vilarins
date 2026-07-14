# cftv-btc

MVP de cadeia de custodia verificavel para videos CFTV usando OpenTimestamps e Bitcoin.

O objetivo e demonstrar que um video pode ser segmentado, hasheado, empacotado, assinado e posteriormente verificado contra uma prova publica de anterioridade temporal ancorada em Bitcoin via OpenTimestamps.

Bitcoin nao armazena o video nem os hashes individuais dos segmentos. O sistema usa Bitcoin apenas como camada publica de timestamp para o manifesto assinado do pacote.

## Entrega

Artigo web:

```text
https://cftv.vilarins.cloud
```

Secao do problema:

```text
https://cftv.vilarins.cloud/#problema
```

Slides da apresentacao:

```text
https://cftv.vilarins.cloud/slides.html
```

Prints de prova:

```text
https://cftv.vilarins.cloud/provas.html
```

Video de apresentacao:

```text
https://youtu.be/PR9o8jA2Crk
```

## Fluxo do MVP

```text
video.mp4
  -> segmentacao em blocos
  -> SHA-256 por segmento
  -> hour_manifest.json
  -> assinatura do manifesto
  -> pacote SIP BagIt
  -> validacao pelo gateway
  -> OpenTimestamps do manifesto
  -> verificacao independente com prova .ots
```

## Estrutura

- `data/input/`: video original de teste.
- `data/segments/`: segmentos gerados pelo segmentador.
- `data/packages/`: pacotes SIP BagIt.
- `data/tampered/`: copias adulteradas para testes.
- `data/ots/`: area auxiliar para provas OpenTimestamps.
- `keys/`: chaves do dispositivo de borda simulado.
- `src/segmenter/`: segmentacao do video.
- `src/packager/`: hashes, manifesto, assinatura e pacote.
- `src/gateway/`: validacao de pacote antes do timestamp.
- `src/anchor/`: carimbo OpenTimestamps.
- `src/verifier/`: verificador independente.
- `reports/`: relatorios de verificacao.
- `docs/mvp/`: documentacao de execucao.

## Decisoes atuais

- O Raspberry Pi nao e dependencia do primeiro MVP.
- O container simula o dispositivo de borda.
- OpenTimestamps e usado como camada de timestamp publico.
- Nao ha wallet BTC no MVP.
- Nao ha Solidity, contrato inteligente, Hardhat ou Lightning no MVP.
- O foco inicial e provar integridade, completude, ordem temporal, assinatura e existencia temporal do manifesto.

## Dependencias

- Python 3.
- `ffmpeg` e `ffprobe`.
- `openssl`.
- Cliente OpenTimestamps:

```text
pip install opentimestamps-client
```

## Execucao local

Gere um video de teste:

```text
bash scripts/generate_sample_video.sh
```

Depois rode o fluxo:

```text
python3 src/segmenter/segment_video.py
python3 src/packager/create_package.py
python3 src/gateway/validate_package.py
python3 src/anchor/stamp_manifest.py
python3 src/verifier/verify_package.py
```

Logo apos o stamp, o status pode ser `PENDENTE_BITCOIN`. Isso significa que o pacote local esta integro e a prova `.ots` existe, mas os calendars ainda nao retornaram uma attestation confirmada em bloco Bitcoin.

Se a prova OpenTimestamps ainda estiver pendente, rode depois:

```text
ots upgrade data/packages/camera-001-20260615T210000Z/timestamp/hour_manifest.json.ots
python3 src/verifier/verify_package.py
```

Para testar apenas a cadeia local antes de gerar `.ots`:

```text
python3 src/verifier/verify_package.py --skip-ots
```

Para aceitar a pendencia de confirmacao Bitcoin como sucesso operacional durante a demo:

```text
python3 src/verifier/verify_package.py --allow-pending
```

## Criterio de sucesso

O MVP sera considerado funcional quando produzir dois resultados:

```text
pacote original + prova .ots -> verificador retorna INTEGRO
pacote adulterado -> verificador identifica a falha
```
