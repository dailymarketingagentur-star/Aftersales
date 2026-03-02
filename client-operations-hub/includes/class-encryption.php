<?php
/**
 * AES-256-CBC encryption for API keys.
 *
 * @package ClientOperationsHub
 */

namespace COH;

defined( 'ABSPATH' ) || exit;

class Encryption {

    private const METHOD = 'aes-256-cbc';

    /**
     * Get or generate the encryption key.
     *
     * The key is stored as a WordPress option.  For production, consider
     * defining it as a constant in wp-config.php instead.
     */
    private static function get_key(): string {
        if ( defined( 'COH_ENCRYPTION_KEY' ) ) {
            return COH_ENCRYPTION_KEY;
        }

        $key = get_option( 'coh_encryption_key' );
        if ( ! $key ) {
            $key = base64_encode( random_bytes( 32 ) );
            update_option( 'coh_encryption_key', $key, false );
        }

        return base64_decode( $key );
    }

    /**
     * Encrypt a plaintext string.
     *
     * @return array{encrypted: string, iv: string}
     */
    public static function encrypt( string $plaintext ): array {
        $key    = self::get_key();
        $iv_len = openssl_cipher_iv_length( self::METHOD );
        $iv     = random_bytes( $iv_len );

        $encrypted = openssl_encrypt( $plaintext, self::METHOD, $key, 0, $iv );

        return array(
            'encrypted' => $encrypted,
            'iv'        => base64_encode( $iv ),
        );
    }

    /**
     * Decrypt a ciphertext.
     */
    public static function decrypt( string $encrypted, string $iv_base64 ): string {
        $key = self::get_key();
        $iv  = base64_decode( $iv_base64 );

        $decrypted = openssl_decrypt( $encrypted, self::METHOD, $key, 0, $iv );

        return $decrypted !== false ? $decrypted : '';
    }
}
