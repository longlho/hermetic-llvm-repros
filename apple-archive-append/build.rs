fn main() {
    let target = std::env::var("PROBE_TARGET").expect("PROBE_TARGET");
    let source = std::env::var("PROBE_SOURCE").expect("PROBE_SOURCE");
    let mut build = cc::Build::new();
    build.target(&target).cargo_metadata(false);
    for i in 0..101 {
        build.file(format!("{source}/unit_{i:03}.c"));
    }
    build.compile("probe");
}
