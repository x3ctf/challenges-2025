use aes_gcm::aead::Aead;
use aes_gcm::{Aes256Gcm, KeyInit, Nonce}; // Or `Aes128Gcm`
#[cfg(target_os = "linux")]
#[cfg(not(debug_assertions))]
use debugoff;
use fancy::printcoln;
use hex;
use inquire::Text;

//fn encrypt_flag(flag: &str, key: &str) -> String {
//    let key_bytes = key.as_bytes();
//    assert_eq!(key_bytes.len(), 32, "Key must be 32 bytes long");
//    let cipher = Aes256Gcm::new_from_slice(key_bytes).expect("Failed to create cipher");
//    let mut nonce_bytes = [0u8; 12];
//    OsRng.fill_bytes(&mut nonce_bytes);
//    let nonce = Nonce::from_slice(&nonce_bytes); // 96-bits; unique per message
//    let ciphertext = cipher
//        .encrypt(nonce, flag.as_bytes())
//        .expect("Encryption failed");
//    let mut encrypted_data = nonce_bytes.to_vec();
//    encrypted_data.extend_from_slice(&ciphertext);
//    hex::encode(encrypted_data)
//}

fn decrypt_flag(encrypted: &str, key: &str) -> String {
    #[cfg(target_os = "linux")]
    #[cfg(not(debug_assertions))]
    debugoff::multi_ptraceme_or_die();

    let key_bytes = key.as_bytes();
    assert_eq!(key_bytes.len(), 32, "Key must be 32 bytes long");
    let encrypted_data = hex::decode(encrypted).expect("Failed to decode hex");
    let (nonce_bytes, ciphertext) = encrypted_data.split_at(12); // 12 bytes for nonce
    let cipher = Aes256Gcm::new_from_slice(key_bytes).expect("Failed to create cipher");
    let plaintext = cipher
        .decrypt(Nonce::from_slice(nonce_bytes), ciphertext)
        .expect("Decryption failed");
    String::from_utf8(plaintext).expect("Failed to convert to UTF-8")
}
fn key_length(key: &str) -> bool {
    key.len() == 32
}

fn main() {
    #[cfg(target_os = "linux")]
    #[cfg(not(debug_assertions))]
    debugoff::multi_ptraceme_or_die();

    printcoln!("[green|bold]Welcome to the flag checker!");
    // let key = "blahajs_for_the_win_c6e3a9b36269";
    let key = Text::new("What's the secret password 🔑?")
        .prompt()
        .unwrap();

    #[cfg(target_os = "linux")]
    #[cfg(not(debug_assertions))]
    debugoff::multi_ptraceme_or_die();

    if !key_length(key.as_str()) {
        printcoln!("[red|bold]The key must be 32 characters long!");
        return;
    }
    if !check(key.as_str()) {
        printcoln!("[red|bold]The key is incorrect! :c");
        return;
    }
    printcoln!("[green]Decrypting the flag, let's see...");
    let flag = "22c4af881035caee0ec32b739c980710e6cc0b370e13da3b7daf0476088ea6e72540774e9a6f186aee129cc96292b8fa89f9155d";
    #[cfg(target_os = "linux")]
    #[cfg(not(debug_assertions))]
    debugoff::multi_ptraceme_or_die();

    let decrypted = decrypt_flag(&flag, key.as_str());
    printcoln!("[green]The flag is: [yellow|bold]{}", decrypted);
}

// fn encrypt(ascii: &str) -> Vec<f64> {
//     let mut result = Vec::new();
//     let mut i = 0;
//     let mut f = 0.00;
//     for c in ascii.chars() {
//         let c = (c as i32 - 3) as u8 as char;
//         println!("{}", c as i32);
//         f = f / 1000.0 + c as i32 as f64 / 1000.0;
//         i += 1;
//         if i == 2 {
//             f = f + 0.0000001;
//             result.push(f);
//             f = 0.00;
//             i = 0;
//         }
//     }
//     if i > 0 {
//         result.push(f);
//     }
//     result
// }
//
// fn decrypt(encrypted: Vec<f64>) -> String {
//     let mut result = String::new();
//     for f in encrypted {
//         let mut f = f;
//         let mut current: Vec<char> = Vec::new();
//         for _ in 0..2 {
//             let mut c = ((f * 1000.0) as i32) as u8;
//             f = f * 1000.0 - c as f64;
//             println!("{}", c as i32);
//             c += 3;
//             current.push(c as char);
//         }
//         result.push_str(&current.iter().rev().collect::<String>());
//     }
//     result
// }

fn check(input: &str) -> bool {
    #[cfg(target_os = "linux")]
    #[cfg(not(debug_assertions))]
    debugoff::multi_ptraceme_or_die();
    let ct = vec![
        0.1050951,
        0.1010941,
        0.1030941,
        0.0921121,
        0.1080991,
        0.0921111,
        0.10111310000000001,
        0.0920981,
        0.1021161,
        0.0921071,
        0.0510961,
        0.048098100000000005,
        0.0540941,
        0.0480951,
        0.047051100000000005,
        0.054051100000000005,
    ];
    let mut result = String::new();
    for f in ct {
        let mut f = f;
        let mut current: Vec<char> = Vec::new();
        for _ in 0..2 {
            let mut c = ((f * 1000.0) as i32) as u8;
            f = f * 1000.0 - c as f64;
            c += 3;
            current.push(c as char);
            #[cfg(target_os = "linux")]
            #[cfg(not(debug_assertions))]
            debugoff::multi_ptraceme_or_die();
        }
        result.push_str(&current.iter().rev().collect::<String>());
    }
    #[cfg(target_os = "linux")]
    #[cfg(not(debug_assertions))]
    debugoff::multi_ptraceme_or_die();
    return input == result;
}
