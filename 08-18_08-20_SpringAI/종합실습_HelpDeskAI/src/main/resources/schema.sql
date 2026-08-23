create table if not exists helpdesk_chat_memory (
  conversation_id varchar(300) not null,
  seq bigint not null,
  message_type varchar(20) not null,
  message_text clob not null,
  primary key (conversation_id, seq)
);
