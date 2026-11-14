# PROJETO - Módulo de Inadimplência e Declaração de Nada Consta

## 1. Visão Geral
Este documento define a especificação completa para o desenvolvimento do **Módulo de Inadimplência, Cobrança e Declaração de Nada Consta (Quitação Condominial)** para o condomínio.

---

## 2. Regras de Negócio e Cálculos Definidos

### 2.1. Parâmetros de Cobrança com Versionamento Histórico (CRUD com Vigência)
Para garantir precisão contábil e conformidade legal com alterações de convenção ao longo dos anos, os parâmetros de cobrança são versionados com vigência (**Data Início** e **Data Fim**):
- **Tabela Histórica de Parâmetros (`ParametroCobranca`):**
  - `data_inicio`: Data inicial em que a regra passou a valer.
  - `data_fim`: Data final de vigência (nula para a regra atualmente ativa).
  - `tipo_multa`: Valor Fixo (R$) ou Percentual (%).
  - `valor_multa`: Valor em R$ ou percentual de multa.
  - `percentual_juros_dia`: Taxa diária de juros (*pro-rata die*).
  - `qtd_parcelas_ajuizamento`: Limite de cotas para alerta de cobrança jurídica.
  - `email_cobranca`, `telefone_cobranca`.
  - `prazo_negociacao_info`, `aviso_protesto_info`, `aviso_ajuizamento_info`, `mensagem_email_padrao`.

### 2.2. Regra de Cálculo com Base no Histórico (Definição Aprovada)
- **Critério da Data de Vencimento (Opção A):** Cada cota busca o parâmetro que estava em vigor na sua **data original de vencimento** (`data_inicio <= data_vencimento` e (`data_fim >= data_vencimento` ou `data_fim is null`)) e calcula a multa e os juros com base nessa regra.
- **Fechamento Automático de Vigências:** Ao cadastrar uma nova vigência iniciando em determinada data (ex: `01/01/2027`), o sistema encerra automaticamente a vigência imediatamente anterior preenchendo sua `data_fim` com o dia anterior (`31/12/2026`).

### 2.2. Origem dos Débitos e Cotas Retroativas
- Débitos em atraso originam-se das cotas (`ReceitaCotaCondominial`) com status pendente e data de vencimento ultrapassada (`data_vencimento < hoje`).
- Débitos históricos de gestões anteriores serão cadastrados diretamente como cotas retroativas pendentes com suas datas originais de vencimento e valores históricos (ex: R$ 330, R$ 360, R$ 380).

### 2.3. Gestão de Acordos, Descontos e Negociações
- O síndico poderá registrar **Acordo / Desconto de Cobrança** para uma ou mais cotas:
  - Possibilidade de conceder isenção ou abatimento de juros/multa (exemplo real: condômino paga apenas o principal da cota mediante acordo).
  - Registro de observação de negociação (ex: `"PAGO 05/11/26 R$ 380,00 - Acordo de isenção de encargos aprovado pelo síndico"`).
  - Quitação ou baixa automática após o pagamento acordado.

### 2.4. Baixa de Cotas em Atraso e Fluxo Contábil (Abordagem A - Regime de Caixa)
Para permitir que o síndico liquide cotas em atraso de meses anteriores ou gestões passadas sem desarmar balancetes históricos já homologados, adota-se a **Abordagem A (Regime de Caixa Automático)**:
1. **Baixa Cadastral da Cota Original (`ReceitaCota`):**
   - A cota atrasada é atualizada para `status = PAGO`, registrando `data_pagamento`, `cota` (principal), `juros_multa` e `valor_pago` efetivo.
   - A baixa é permitida mesmo se o período original da cota estiver `FECHADO`, desde que acionada por usuário com permissão de gestão (síndico/administrador).
   - Com o status `PAGO`, a cota deixa de constar como débito no painel de inadimplência e a unidade torna-se elegível para a **Declaração de Nada Consta**.
2. **Registro Contábil no Período Aberto (`ReceitaExtra`):**
   - Caso a cota pertença a um período anterior já `FECHADO` (ou histórico), o sistema cria automaticamente um lançamento de receita no **período de prestação atualmente ABERTO** do condomínio:
     - Principal da cota: `ReceitaExtra` do tipo `COTA_ATRASADA` com a descrição: *"Recuperação Cota Atrasada - Casa XX - Ref. MM/AAAA"*.
     - Encargos (se houver): `ReceitaExtra` do tipo `JUROS_MULTA` com a descrição: *"Encargos/Multa/Juros Cota - Casa XX - Ref. MM/AAAA"*.
   - Caso a cota seja do próprio período que ainda está `ABERTO`, ela apenas computa normalmente na linha regular de cotas do período, sem duplicidade.
3. **Dados e Controles da Baixa:**
   - **Data do Pagamento:** Data informada do recebimento (default: data atual).
   - **Valor Pago Efetivo:** Valor digitado pelo síndico, permitindo conceder descontos/isenção nos juros e multas calculados.
   - **Observação / Justificativa:** Texto explicativo registrado na cota e na receita extra.
   - **Comprovante:** Upload opcional do comprovante de pagamento.

---

## 3. Funcionalidades do Módulo

### 3.1. Visão Síndico / Gestão

1. **Dashboard / Painel Geral de Inadimplência:**
   - Lista consolidada de unidades inadimplentes com total de parcelas em atraso, principal, multas, juros e saldo devedor consolidado.
   - Indicadores visuais de criticidade (ex: alerta vermelho para unidades com 6+ cotas em atraso sujeitas a ajuizamento).
   - Exportação geral em PDF e Excel para prestação de contas e assembleias.

2. **Emissão da Carta / Ficha de Cobrança ("Aviso de Débito em Atraso"):**
   - Layout idêntico ao modelo oficial:
     - Cabeçalho: Condomínio, CNPJ, Endereço e Data de Atualização.
     - Destinatário: Nome do condômino/proprietário e identificação da casa/unidade.
     - Texto de notificação amigável e explicativa.
     - Tabela analítica: Item, Data Atualização, Vencimento, Dias Vencidos, Taxa, Multa, Juros, Total a Pagar e Observações.
     - Totalizadores: Saldo devedor discriminado (soma de taxas, multas, juros e total geral).
     - Alertas jurídicos e prazos de negociação.
     - Contatos da administração.

3. **Disparo de Cobrança por E-mail:**
   - Disparo individual ou em lote.
   - **Edição Livre do Conteúdo:** O síndico poderá editar livremente o texto do e-mail no momento do envio para cada morador, permitindo personalizar completamente a mensagem (recados pontuais, lembretes de prazos, negociações específicas).
   - **Anexo Obrigatório:** O e-mail sempre acompanhará o PDF oficial do "Aviso de Débito em Atraso" gerado e anexado.
   - **Histórico de Envios:** Registro de cada e-mail disparado contendo data/hora, destinatário, texto exato enviado, remetente e status do envio.

4. **Gerenciador de Declarações de Nada Consta Emitidas:**
   - Visualização e consulta de todas as certidões emitidas no período.

5. **Baixa de Cotas em Atraso (Individual e em Lote):**
   - Disponível na Ficha Analítica de Débitos da unidade (`InadimplenciaView`).
   - Botão **"Dar Baixa"** em cada linha da cota pendente ou seleção de múltiplas cotas para **"Baixar Selecionadas"**.
   - Modal com cálculo de encargos em tempo real, ajuste de valor pago (com suporte a descontos concedidos), preenchimento de data de pagamento, observações e comprovante.
   - Atualização automática do status da cota e inclusão contábil no período aberto ativo (Abordagem A).

---

### 3.2. Visão Condômino / Morador (Multi-Unidades)

1. **Autoatendimento com Múltiplas Casas:**
   - O morador com mais de uma unidade (ex: Maylla com Casas 04, 05, 10, 11, 12, etc.) pode visualizar os débitos de **cada unidade separadamente** ou na opção **"Todas as Unidades (Visão Consolidada)"**.
   - **Emissão de Débitos "Tudo Junto":** Reúne todos os títulos pendentes de todas as casas do condômino em uma única ficha/PDF de aviso de débito consolidado.
   - **Emissão de Nada Consta "Tudo Junto":** Gera a declaração concatenando todas as casas que estiverem **adimplentes**, permitindo quitação geral mesmo que alguma outra unidade isolada ainda tenha pendência.

---

### 3.3. Filtros na Tela de Vínculos (`/vinculos`)
- **Filtro de Pessoa no Modal de Vínculo:**
  - Adicionado campo de busca textual em tempo real para pesquisar pessoas por nome ou CPF no modal existente de cadastro de vínculo (idêntico ao filtro já existente para unidades).

2. **Cenário A: Condômino com Débito(s) em Aberto:**
   - Acesso imediato à sua planilha de débitos atualizada.
   - Visualização dos encargos detalhados e possibilidade de baixar o PDF do Aviso de Débito.
   - Instruções de quitação (chave PIX, dados bancários e canal para envio de comprovante).
   - Opção para solicitar proposta de negociação/acordo com o síndico.

3. **Cenário B: Condômino Adimplente (Sem Débitos):**
   - O sistema valida automaticamente se a unidade não possui cotas pendentes vencidas até a presente data.
   - Botão em destaque: **"Emitir Declaração de Nada Consta"**.
   - Geração imediata em PDF conforme o modelo oficial:
     - Dados do Condomínio (Nome, CNPJ, Endereço).
     - Cidade e Data de Emissão (ex: *Fortaleza, DD de Mês de AAAA*).
     - Identificação do Síndico em exercício (Nome, CPF, Endereço).
     - Identificação do Condômino e Unidade (Nome, CPF, Casa/Unidade).
     - Texto formal atestando a inexistência de pendências financeiras.
     - Menção explícita ao último pagamento registrado: *"Consta como último pagamento a cota condominial referente ao mês de [MÊS/ANO], com vencimento em [DD/MM/AAAA]"*.
     - **Validade Expressa:** *"Declaração válida até [Último dia do mês corrente]"*.
     - Linha de assinatura do Síndico e código autenticador / validação eletrônica.

---

## 4. Modelagem e Estrutura Técnica

### 4.1. Backend (Django)
- **Model `ConfiguracaoCobranca` (Singleton ou por Condomínio):**
  - `tipo_multa` (FIXO / PERCENTUAL)
  - `valor_multa` (ex: 10.00)
  - `percentual_juros_dia` (ex: 0.0024 -> 0.24% ao dia)
  - `dias_limite_ajuizamento` (default: 6 meses / parcelas)
  - `email_cobranca`, `telefone_cobranca`
  - `texto_aviso_rodape`, `observacoes_padrao`

- **Model `CertidaoNadaConsta`:**
  - `condominio`, `unidade`, `solicitante`
  - `codigo_validacao` (UUID ou Hash alfanumérico curto para conferência)
  - `data_emissao`, `data_validade` (sempre último dia do mês corrente)
  - `ultima_cota_paga_referencia`, `ultima_cota_paga_vencimento`
  - `sindico_nome`, `sindico_cpf`
  - `arquivo_pdf`

- **Model `HistoricoNotificacaoCobranca`:**
  - `unidade`, `destinatario_email`, `mensagem_personalizada`, `valor_total_notificado`, `enviado_por`, `data_envio`, `status_envio`

- **Services:**
  - `CalculadoraDebitoService`: Realiza a apuração dinâmica dos dias de atraso, juros e multas para qualquer cota ou período.
  - `PdfCobrancaService`: Gera o PDF da carta de cobrança idêntico ao modelo da planilha.
  - `PdfNadaConstaService`: Gera a certidão em PDF idêntica ao modelo anexado.
  - `EmailCobrancaService`: Envia e-mail formatado com personalização do síndico e anexo PDF.

### 4.2. Frontend & Painel Admin
- **Área Administrativa (Síndico):**
  - Menu **Inadimplência**:
    - Tabela de inadimplentes com filtros e ações rápidas.
    - Modal de visualização da Ficha de Cobrança.
    - Modal de envio de e-mail com campo de texto customizado e preview antes do disparo.
    - Painel de configuração de parâmetros de juros/multa.
- **Área do Morador:**
  - Menu **Minhas Finanças / Quitação**:
    - Card com status da unidade: "Em dia" ou "Pendente".
    - Se pendente: grade de débitos atualizada e botão para baixar o espelho de cobrança.
    - Se em dia: botão "Emitir Nada Consta" que baixa o PDF oficial com a validade do mês.

---

## 5. Implementação Realizada & Status Atual

### 5.1. Histórico de Parâmetros de Cobrança (Opção A Implementada)
- Parâmetros vigentes por período (`data_inicio` e `data_fim`).
- A regra de juros diários (*pro-rata die*) e multa é determinada pela **data de vencimento original da cota**.
- Fechamento automático de vigência anterior ao cadastrar uma nova vigência a partir de uma data específica.

### 5.2. Múltiplas Unidades por Condômino ("Meu Espaço")
- Suporte a condôminos proprietários de múltiplos imóveis (ex: usuária Maylla com Casas 04, 05, 07, 10, 11, 12, 13, 14):
  - **Visualização por Unidade:** O condômino pode alternar entre unidades individuais ou a opção **"Todas as Unidades (Tudo Junto)"**.
  - **Aviso de Débito Consolidado:** Emissão unificada de débitos em atraso de todas as casas do proprietário em um único PDF.
  - **Declaração de Nada Consta Consolidada ("Tudo Junto"):**
    - Emite a declaração de quitação oficial para todas as casas que estiverem **adimplentes**.
    - Concatena as certidões em um único arquivo PDF oficial (1 página para cada unidade adimplente, com código autenticador individual, menção à última cota paga e validade até o fim do mês corrente).
    - Unidades com pendências não são emitidas e permanecem listadas no aviso de débito.

### 5.3. Filtro em Tempo Real no Vínculo Pessoa-Unidade (`/vinculos`)
- Campo de busca em tempo real para pesquisar **Pessoas por Nome ou CPF** dentro do modal de novo/edição de vínculo (idêntico ao filtro existente para Unidades).
- Reset automático dos filtros a cada abertura do modal.

### 5.4. Isolamento e Filtro de Cotas em Prestações Publicadas (`/prestacao/morador`)
- **Restrição a Prestações Publicadas:** A seção *"Minhas Cotas Condominiais"* agora filtra estritamente cotas pertencentes a prestações com status `PUBLICADO` (removendo períodos em aberto ou não homologados como Novembro/2026).
- **Isolamento de Unidades do Usuário:** Retorna somente as cotas das unidades com vínculo ativo (`data_fim__isnull=True`) da pessoa associada ao usuário autenticado e do condomínio ativo.
- **Seletores no Frontend:**
  - **Desacoplamento Completo:** A seleção de prestação/balancete no topo da página altera estritamente os cards e demonstrativos do condomínio, não interferindo na listagem histórica de *"Minhas Cotas Condominiais"*.
  - Seletor de Unidades para usuários multi-casas: opção *"Todas as Minhas Unidades"* ou seleção individual de qualquer uma de suas casas.
  - Indicadores e contadores de cotas (quitadas, pendentes, isentas) recalculados dinamicamente com base na unidade selecionada.

---

## 6. Próxima Etapa: Baixa de Cotas em Atraso pelo Síndico (Especificação Aprovada)

### 6.1. Backend
- **Endpoint de Baixa de Cota em Atraso (`POST /api/financeiro/cotas/{id}/dar-baixa-atrasada/` ou ação em `ReceitaCotaViewSet`):**
  - Aceita payload com `data_pagamento`, `valor_pago`, `cota` (principal), `juros_multa`, `observacao`, `comprovante`.
  - Permite a operação mesmo com o período da cota `FECHADO`, validando permissão de gestão do usuário autenticado.
  - Atualiza `cota.status = PAGO`, `cota.data_pagamento`, `cota.valor_pago`, `cota.observacao`.
  - **Regime de Caixa Automático (Abordagem A):**
    - Se o período da cota estiver `FECHADO` (ou se for cota histórica de período anterior), localiza o período de prestação `ABERTO` do condomínio correspondente.
    - Cria os registros em `ReceitaExtra`:
      - `COTA_ATRASADA`: valor principal recebido (`cota.cota` ou `cota.valor_titulo`).
      - `JUROS_MULTA`: encargos efetivamente pagos (`cota.juros_multa`), se maior que zero.
  - Caso a cota seja do período atualmente aberto, apenas atualiza a cota regular diretamente sem duplicar em receita extra.
- **Endpoint de Baixa em Lote (`POST /api/financeiro/cotas/dar-baixa-atrasadas-lote/`):**
  - Permite liquidar múltiplas cotas selecionadas da mesma unidade em uma única operação.

### 6.2. Frontend
- **Ficha de Cobrança / Espelho da Unidade (`InadimplenciaView.vue`):**
  - Coluna de Ações na tabela de itens de débitos da unidade com botão **"Baixar"** (ícone de check/dinheiro).
  - Checkbox por linha para seleção múltipla e botão **"Baixar Cotas Selecionadas"**.
  - Modal intuitivo de confirmação de baixa exibindo:
    - Unidade e competência(s) selecionada(s).
    - Discriminação (Principal + Encargos calculados).
    - Campo para data de pagamento (default: hoje).
    - Campo de valor pago efetivo (editável com alerta caso haja concessão de desconto).
    - Campo de observações (ex: "Acordo verbal", "PIX recebido").
    - Upload de comprovante.
  - Recarregamento automático do relatório de inadimplência após a baixa com notificação toast de sucesso.

### 6.3. Validação e Testes
- Teste 1: Baixa de cota de período anterior fechado -> verificar status `PAGO`, liberação da certidão de Nada Consta e criação da `ReceitaExtra` no período aberto.
- Teste 2: Baixa com valor ajustado (desconto em juros/multa) -> verificar cálculo e observação gravada.
- Teste 3: Baixa em lote de múltiplas cotas da mesma unidade.
