fn main() {
    let features = std::env::var("CARGO_CFG_TARGET_FEATURE").unwrap();
    assert!(features.split(',').any(|feature| feature == "crt-static"), "target cfg omits crt-static: {features}");
}
