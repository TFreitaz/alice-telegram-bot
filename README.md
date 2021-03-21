# Alice Telegram Bot

<p>Alice é uma personalidade robótica para te acompanhar do seu dia-a-dia. Seja com lembretes, informações ou entretenimento, ela está aqui para ser amigável e útil a você.</p>

## Sumário
* Começando a conversar
* Funcionalidades

## Começando a conversar

<p>Para ter acesso à Alice, baixe o aplicativo do Telegram para <a href=https://play.google.com/store/apps/details?id=org.telegram.messenger&hl=pt_BR&gl=US>Android</a> ou <a href=https://apps.apple.com/br/app/telegram-messenger/id686449807>iOS</a>, ou acesse a <a href=https://web.telegram.org/#/login>versão web</a> no seu navegador.</p>

<p>No Telegram, busque pelo usuário <i>@alice_zbot</i> ou <a href=https://t.me/alice_zbot>clique aqui</a>. Você será direcionado ao chat <b>Alice</b>.</p>

<p>Agora, se essa for a sua primeira conversa com a Alice, verá um grande botão escrito <b>Start</b>. Clique nele, e ela te atenderá. Caso já tenha um histórico de conversa com ela, não verá o botão, mas também terá o mesmo resultado se enviar uma mensagem com o comando <code>/start</code>. Ou ainda, você pode pular esta etapa e já partir para a conversa.</p> 

<p>A Alice é desenvolvida visando ter uma conversa natural com o usuário. Dessa forma, esperamos que você consiga usar suas funcionalidades apenas pedindo, como faria com um humano qualquer. Ainda assim, todas as ações podem ser acionadas através de comandos iniciados com uma barra (<code>/</code>). Para ter uma lista de todas as funcionalidades disponíveis, basta enviar o comando <code>/help</code>.</p>

## Funcionalidades

### Dados do usuário
<p><b>Definir nome:</b> Ensina à Alice como te chamar. Pode ser seu nome, apelido, um pronome de tratamento, ou o que preferir. Enquanto você não definir um nome, Alice te avisará que não sabe como te chamar. Para registrar seu nome ou apelido, basta enviar uma mensagem com o comando <code>/definir_nome</code> seguido do nome pelo qual quer ser chamado.</p>
<p>Exemplos: </p>

* ``/definir_nome Leandro``
* ``/definir_nome Tony Stark``
* ``/definir_nome senhor Spock``
* ``/definir_nome Dr. House``

### Lembretes

<p><b>Criar lembrete:</b> programa uma data e horário para Alice te lembrar de algo. Pode ser acionado tanto através de conversa natural quanto pelo comando <code>/lembrete</code>. Você pode definir um título para o lembrete ao passá-lo entre aspas duplas. Alice se esforçará para reconhecer a data e horário do seu lembrete da forma que você escrever, mas na dúvida, use o formado horas:minutos e dia/mês/ano. Ok, o ano a Alice garante.</p>
<p>Para definir o horário do lembrete, você pode usar o modelo horas:minutos, passar apenas as horas de forma numérica, ou o período do dia como manhã (08:00h), tarde (16:00h), noite (20:00h) ou madrugada (03:00h). Caso não seja reconhecido um horário, o lembrete será definido para uma hora a partir do momento da mensagem.</p>
<p>Na definição da data, como já dito, pode ser usado dia/mês/ano, ou simplesmente dia/mês, caso o ano seja o atual. Ainda é possível passar o dia como "hoje" ou "amanhã". Se nenhuma data for reconhecida, será definida a primeira data possível para o horário informado (hoje ou amanhã).</p>
<p>Exemplos</p>

* ``Alice, me lembre de "Pagar boleto" às 13 horas.``
* ``Marque um lembrete para essa tarde chamado "Jogo do barça".``
* ``Me lembre de "Fazer bolo" amanhã às 15:00h.``
* ``Defina um lembrete para dia 22/04 às 10:00.``
* ``/lembrete "Falar com meu pai" hoje de noite``
* ``/lembrete``
