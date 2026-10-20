unsafe extern "C" {
    fn native_add(left: i32, right: i32) -> i32;
}

fn main() {
    assert_eq!(unsafe { native_add(1, 2) }, 3);
}
