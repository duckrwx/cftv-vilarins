# Testes de adulteracao

O MVP inclui testes controlados para demonstrar deteccao de alteracoes posteriores ao pacote assinado e timestampado.

## Gerar casos adulterados

```text
bash scripts/make_tampered_cases.sh
```

Casos gerados:

```text
data/tampered/case-01-segment-bytes-modified
data/tampered/case-02-segment-removed
data/tampered/case-03-manifest-modified
data/tampered/case-04-segment-reordered-in-manifest
```

## Rodar verificacao dos casos

```text
for case in data/tampered/case-*; do
  name=$(basename "$case")
  python3 src/verifier/verify_package.py \
    --package "$case" \
    --public-key keys/device_public.pem \
    --skip-ots \
    --report "reports/${name}_report.json" || true
done
```

O `|| true` e intencional: nos casos adulterados, o verificador retorna erro operacional para indicar que o pacote foi reprovado.

## Matriz de resultados esperados

| Caso | Alteracao | Resultado esperado |
|---|---|---|
| case-01 | bytes adicionados em `segment_0001.mp4` | checksum divergente e hash do segmento divergente |
| case-02 | remocao de `segment_0002.mp4` | arquivo ausente e segmento ausente |
| case-03 | alteracao de `camera_id` no manifesto | checksum do manifesto divergente e assinatura invalida |
| case-04 | reordenacao de segmentos no manifesto | checksum do manifesto divergente, assinatura invalida e sequencia invalida |

## Interpretacao

Esses testes demonstram que o sistema detecta:

- alteracao do conteudo de segmento;
- remocao de segmento;
- modificacao do manifesto;
- reordenacao temporal;
- quebra de assinatura.

OpenTimestamps entra para provar anterioridade temporal do manifesto integro, nao para substituir os checksums e a assinatura.

