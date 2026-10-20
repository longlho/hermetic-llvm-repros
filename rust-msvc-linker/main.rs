unsafe extern "C" { fn native_value() -> u32; }
fn main() { assert_eq!(unsafe { native_value() }, 42); }
