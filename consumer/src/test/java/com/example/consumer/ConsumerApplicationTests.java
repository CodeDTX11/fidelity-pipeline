package com.example.consumer;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = {
		"spring.main.lazy-initialization=true",
		"spring.autoconfigure.exclude=" +
				"org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration," +
				"org.springframework.boot.data.jdbc.autoconfigure.DataJdbcRepositoriesAutoConfiguration"
})
class ConsumerApplicationTests {

	@Test
	void contextLoads() {
	}

}
