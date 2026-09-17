## Descrizione

<!-- Describe brevemente il cambio -->

## Tipo di cambio

- [ ] Bug fix
- [ ] Nuova feature
- [ ] Refactor
- [ ] Documentazione
- [ ] Aggiornamento dati

## Checklist

- [ ] `dataset.yml` valido (`toolkit inspect config`)
- [ ] `toolkit run` ok su tutti gli anni
- [ ] `clean.sql` usa macro standard (no boilerplate)
- [ ] `mart*.sql` legge solo da `clean_input`
- [ ] `validate` dichiarato (min_rows, not_null, primary_key)
- [ ] Nessun file dati committato in root
- [ ] Output in `.gitignore`
- [ ] Dashboard funziona (`streamlit run app.py`)

## Note aggiuntive

<!-- Opzionale: link a issue, screenshot, dati mancanti -->
