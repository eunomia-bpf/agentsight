use super::*;
use crate::runners::{EventStream, FakeRunner, Runner};
use crate::view::MaterializedView;
use futures::stream::StreamExt;
use serde_json::json;
use std::sync::{
    Arc,
    atomic::{AtomicUsize, Ordering},
};

fn materializer() -> MaterializingAnalyzer {
    MaterializingAnalyzer::with_view(MaterializedView::shared_bounded())
}

#[tokio::test]
async fn test_complex_analyzer_chain_composition() {
    struct FilterAnalyzer;

    #[async_trait]
    impl Analyzer for FilterAnalyzer {
        async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
            Ok(Box::pin(stream.filter(|event| {
                futures::future::ready(event.source == "ssl")
            })))
        }
    }

    let mut runner = FakeRunner::new()
        .event_count(5)
        .delay_ms(10)
        .add_analyzer(Box::new(FilterAnalyzer))
        .add_analyzer(Box::new(SSEProcessor::new_with_timeout(5000)))
        .add_analyzer(Box::new(HTTPParser::new().disable_raw_data()))
        .add_analyzer(Box::new(materializer()));

    let stream = runner.run().await.unwrap();
    let events: Vec<_> = stream.collect().await;

    assert!(!events.is_empty());
    let non_ssl_events = events
        .iter()
        .filter(|e| e.source != "ssl" && e.source != "sse_processor" && e.source != "http_parser")
        .count();
    assert_eq!(non_ssl_events, 0);
}

#[tokio::test]
async fn test_analyzer_chain_error_resilience() {
    struct ErrorSimulatorAnalyzer {
        error_on_event_number: usize,
    }

    #[async_trait]
    impl Analyzer for ErrorSimulatorAnalyzer {
        async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
            let error_event = self.error_on_event_number;
            let counter = Arc::new(AtomicUsize::new(0));

            let processed_stream = stream.map(move |event| {
                let count = counter.fetch_add(1, Ordering::SeqCst) + 1;
                if count == error_event {
                    let mut error_event = event;
                    if let Some(data) = error_event.data.as_object_mut() {
                        data.insert("analyzer_error".to_string(), json!("Simulated error"));
                    }
                    error_event
                } else {
                    event
                }
            });

            Ok(Box::pin(processed_stream))
        }
    }

    let mut runner = FakeRunner::new()
        .event_count(5)
        .delay_ms(10)
        .add_analyzer(Box::new(ErrorSimulatorAnalyzer {
            error_on_event_number: 3,
        }))
        .add_analyzer(Box::new(SSEProcessor::new_with_timeout(5000)));

    let stream = runner.run().await.unwrap();
    let events: Vec<_> = stream.collect().await;

    assert!(events.len() >= 10);
    let error_events = events
        .iter()
        .filter(|e| e.data.get("analyzer_error").is_some())
        .count();
    assert!(error_events > 0);
}
