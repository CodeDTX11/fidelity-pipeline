package com.example.consumer.kafka;

import com.example.consumer.model.TransactionEvent;
import com.example.consumer.repository.TransactionRepository;
//import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;
import tools.jackson.databind.json.JsonMapper;

@Component
public class TransactionListener {

    private final JsonMapper jsonMapper;
    private final TransactionRepository repo;

    public TransactionListener(JsonMapper jsonMapper, TransactionRepository repo) {
        this.jsonMapper = jsonMapper;
        this.repo = repo;
    }

    @KafkaListener(topics = "transactions.cleaned.v1")
    public void onMessage(ConsumerRecord<String, String> record, Acknowledgment ack) {
        try {
            TransactionEvent event = jsonMapper.readValue(record.value(), TransactionEvent.class);

            int rows = repo.insertIgnoreDuplicate(event);

            // commit offset only after DB work succeeds
            ack.acknowledge();

            System.out.println("processed event_id=" + event.event_id
                    + " inserted=" + (rows == 1)
                    + " partition=" + record.partition()
                    + " offset=" + record.offset());

        } catch (Exception ex) {
            // no ack => Kafka will retry (at-least-once)
            System.err.println("ERROR partition=" + record.partition()
                    + " offset=" + record.offset()
                    + " payload=" + record.value());
            ex.printStackTrace();
        }
    }
}
