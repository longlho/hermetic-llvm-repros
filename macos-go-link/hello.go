package main
/*
static int answer(void) { return 42; }
*/
import "C"
func main() { if C.answer() != 42 { panic("wrong answer") } }
