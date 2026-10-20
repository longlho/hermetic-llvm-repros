fn main() {
    let bindings = bindgen::Builder::default()
        .header(concat!(env!("CARGO_MANIFEST_DIR"), "/probe.hpp"))
        .clang_args(["-x", "c++", "-std=c++17"])
        .formatter(bindgen::Formatter::None)
        .generate()
        .expect("the recursive union template must not panic during layout inference");
    assert!(bindings.to_string().contains("RecursiveUnion"));
}
