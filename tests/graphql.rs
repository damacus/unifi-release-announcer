use serde_json::json;
use unifi_release_announcer::feed::GraphQl;
use wiremock::{
    Mock, MockServer, ResponseTemplate,
    matchers::{body_partial_json, method, path},
};

#[tokio::test]
async fn reads_feed_and_preserves_payload() {
    let server = MockServer::start().await;
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("fixtures/parity.json")).unwrap();
    Mock::given(method("POST"))
        .and(path("/"))
        .and(body_partial_json(
            json!({"variables":{"limit":50,"statuses":["PUBLISHED"]}}),
        ))
        .respond_with(
            ResponseTemplate::new(200)
                .set_body_json(json!({"data":{"releases":{"items":fixture["items"]}}})),
        )
        .expect(1)
        .mount(&server)
        .await;
    let releases = GraphQl::with_url(&server.uri())
        .unwrap()
        .latest(&["unifi-protect".into()])
        .await
        .unwrap();
    assert_eq!(releases.len(), 1);
    assert!(releases[0].url.ends_with("/release-h/h"));
}
#[tokio::test]
async fn empty_feed_is_success() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(json!({"data":{"releases":{"items":[]}}})),
        )
        .mount(&server)
        .await;
    assert!(
        GraphQl::with_url(&server.uri())
            .unwrap()
            .latest(&[])
            .await
            .unwrap()
            .is_empty()
    );
}
#[tokio::test]
async fn errors_and_malformed_responses_are_failures() {
    for response in [
        ResponseTemplate::new(500),
        ResponseTemplate::new(200).set_body_json(
            json!({"errors":[{"message":"untrusted"}],"data":{"releases":{"items":[]}}}),
        ),
        ResponseTemplate::new(200).set_body_json(json!({"data":null})),
        ResponseTemplate::new(200).set_body_string("{"),
        ResponseTemplate::new(200).set_body_json(json!({"data":{"releases":{"items":{}}}})),
    ] {
        let server = MockServer::start().await;
        Mock::given(method("POST"))
            .respond_with(response)
            .mount(&server)
            .await;
        assert!(
            GraphQl::with_url(&server.uri())
                .unwrap()
                .latest(&[])
                .await
                .is_err()
        );
    }
}
#[tokio::test]
async fn release_details_and_not_found() {
    let server = MockServer::start().await;
    Mock::given(body_partial_json(json!({"variables":{"id":"x"}})))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({"data":{"release":{
            "title":"Application","slug":"app","stage":"GA","version":"1","createdAt":"2026-10-01T01:02:03Z",
            "tags":["unifi-protect"],"author":{"username":"test"},"lastActivityAt":"2026-10-01T02:00:00Z"
        }}}))).mount(&server).await;
    Mock::given(body_partial_json(json!({"variables":{"id":"missing"}})))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({"data":{"release":null}})))
        .mount(&server)
        .await;
    let client = GraphQl::with_url(&server.uri()).unwrap();
    let details = client.details("x").await.unwrap().unwrap();
    assert_eq!(details["created_date"], "2026-10-01");
    assert_eq!(details["author"]["username"], "test");
    assert!(client.details("missing").await.unwrap().is_none());
}

#[tokio::test]
async fn incomplete_unrelated_items_do_not_block_configured_releases() {
    let server = MockServer::start().await;
    let fixture: serde_json::Value =
        serde_json::from_str(include_str!("fixtures/parity.json")).unwrap();
    Mock::given(method("POST"))
        .respond_with(
            ResponseTemplate::new(200)
                .set_body_json(json!({"data":{"releases":{"items":fixture["mixed_items"]}}})),
        )
        .mount(&server)
        .await;
    let releases = GraphQl::with_url(&server.uri())
        .unwrap()
        .latest(&["unifi-protect".into()])
        .await
        .unwrap();
    assert_eq!(
        serde_json::to_value(releases).unwrap(),
        fixture["mixed_releases"]
    );
}

#[tokio::test]
async fn malformed_configured_release_still_fails_the_poll() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .respond_with(ResponseTemplate::new(200).set_body_json(
            json!({"data":{"releases":{"items":[{
                "id":"id","title":"UniFi Protect Application","tags":["unifi-protect"],
                "version":null,"createdAt":"2026-10-01T00:00:00Z","slug":"release"
            }]}}}),
        ))
        .mount(&server)
        .await;
    assert!(
        GraphQl::with_url(&server.uri())
            .unwrap()
            .latest(&["unifi-protect".into()])
            .await
            .is_err()
    );
}
