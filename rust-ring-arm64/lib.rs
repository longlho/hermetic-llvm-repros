pub fn digest() -> ring::digest::Digest { ring::digest::digest(&ring::digest::SHA256, b"probe") }
