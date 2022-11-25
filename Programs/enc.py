'''This module helps in performing End to End encryption in the entire project. We use a combination of RSA 
(asymmetric encryption) and (symmetric key block cipher) to encrypt the messages. This modules has two classes 
AESCipher to perform AES encryption and Encryption class, which perfoms E2EE of messages.

Message is encrypted using AES and the AES key is encrypted using RSA.
'''

import rsa
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
# from Crypto.PublicKey import RSA as rsa



class AESCipher(object):
    '''
    Parameters
    ----------
    key : bytes or str
        This key is used to encrypt/decrypt the messages.

    Returns
    -------
    AESCipher object.

    '''

    def __init__(self, key): 
        if not isinstance(key, bytes):
            key = key.encode()
        self.bs = AES.block_size
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, raw):
        '''
        Parameters
        ----------
        raw : str or bytes
            The message that is to be encrypted.

        Returns
        -------
        bytes
            Base 64 encoded encrypted message.
        '''
        try:
            if isinstance(raw, bytes):
                raw = raw.decode()
            raw = self._pad(raw)
            iv = Random.new().read(AES.block_size)
            cipher = AES.new(self.key, AES.MODE_CBC, iv)
            return base64.b64encode(iv + cipher.encrypt(raw.encode()))
            # return iv + cipher.encrypt(raw.encode())
        except Exception as e:
            print('Exception in AESCipher.encrypt', e)
            

    def decrypt(self, enc):
        '''
        Parameters
        ----------
        enc : bytes or str
            Base 64 encoded encrypted message that is to be decrypted.

        Returns
        -------
        bytes
            Decrypted message.

        '''
        enc = base64.b64decode(enc)
        if not isinstance(enc, bytes):
            enc = enc.encode()
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        '''
        Parameters
        ----------
        s : str
            str to be padded.

        Returns
        -------
        str
            Padded string to match AES block size.

        '''
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        '''

        Parameters
        ----------
        s : bytes
            message to be unpadded.

        Returns
        -------
        bytes
            Unpadded message.

        '''
        return s[:-ord(s[len(s)-1:])]
    
    
class Encrypt(object):
    '''
    Parameters
    ----------
    *args : (optional)
        len(args) = 0 : creates Encrypt object with new RSA Private-Public key pair.
        len(args) = 1 : (str) creates Encrypt object with RSA Private-Public keys
        loaded from args[0]_public.pem and args[0]_private.pem

    '''
    
    def __init__(self, *args):
      
        self.private_RSA = 0
        self.public_RSA = 0
        if len(args) == 0:
            self.public_RSA, self.private_RSA = rsa.newkeys(1024)
        elif len(args) == 1:
            self.load_keys(args[0])
 
    def save_private_key(self, *args):
        ''' Return/store RSA private key.
        
        If no argument is given function returns the private key.
        
        If one argument is given, it must be str, private key is stored in the file args[0]_private.pem
        
        Parameters
        ----------
        *args : (optional)

        Returns
        -------
        bytes
            if no argument is given

        '''
        if len(args) == 1:  
            with open(args[0] +'_private.pem', 'wb') as f:
                f.write(self.private_RSA.save_pkcs1('PEM'))
        else:
            return self.private_RSA.save_pkcs1('PEM')
        
    def get_public_key(self, *args):
        ''' Return/store RSA public key.
        
        If no argument is given function returns the public key.
        
        If one argument is given, it must be str, private key is stored in the file args[0]_public.pem
        
        Parameters
        ----------
        *args : (optional)

        Returns
        -------
        bytes
            if no argument is given

        '''
        if len(args) == 1:
            with open(args[0] +'_public.pem', 'wb') as f:
                f.write(self.public_RSA.save_pkcs1('PEM'))
        else:
            return self.public_RSA.save_pkcs1('PEM')
        
    def save_keys(self, file):
        ''' Saves RSA public and private keys to the files 'file_public.pem' and 'file_private.pem' respectively.
    
        Parameters
        ----------
        file : str
            file name.

        Returns
        -------
        None.

        '''
        self.save_private_key(file)
        self.get_public_key(file)
        
    def return_public_key_object(self, public_key):
        ''' Creates RSA.PublicKey object corresponding to the PEM format public key.

        Parameters
        ----------
        public_key : bytes
            PEM format public key.

        Returns
        -------
        RSA.PublicKey
            RSA.PublicKey object.

        '''
        return rsa.PublicKey.load_pkcs1(public_key)
        
    def load_keys(self, file):
        ''' Loads RSA public and private keys from 'file_public.pem' and 'file_private.pem'

        Parameters
        ----------
        file : str
            file name.

        Returns
        -------
        None.

        '''
        with open(file +'_private.pem', 'rb') as f:
            self.private_RSA = rsa.PrivateKey.load_pkcs1(f.read())
        with open(file +'_public.pem', 'rb') as f:
            self.public_RSA = rsa.PublicKey.load_pkcs1(f.read())
            
    def RSA_encrypt(self, message, key):
        ''' RSA encrypts using the PEM format public key provided.

        Parameters
        ----------
        message : bytes or str
            message that is to be RSA encrypted.
        key : bytes
            DESCRIPTION.

        Returns
        -------
        bytes
            Encrypted message.

        '''
        if not isinstance(message, bytes):
            # print(type(message))
            message = message.encode()
        return rsa.encrypt(message, self.return_public_key_object(key))
    
    def RSA_decrypt(self, message):
        ''' RSA decrypts using self.private_key

        Parameters
        ----------
        message : bytes or str
            Message that is to be decrypted.

        Returns
        -------
        bytes or None
            Decrypted message if successful, else returns None.

        '''
        try:
            if not isinstance(message, bytes):
                message = message.encode()
            return rsa.decrypt(message, self.private_RSA)
        except:
            return None
        
    def RSA_sign(self, message):
        ''' Signs the message using self.private_key

        Parameters
        ----------
        message : str or bytes
            message that is to be signed.

        Returns
        -------
        bytes
            Base 64 encoded sign.

        '''
        if not isinstance(message, bytes):
            message = message.encode()
        return base64.b64encode(rsa.sign(message, self.private_RSA, 'SHA-256'))
    
    def RSA_verify(self, message, sign, *args):
        ''' Verifies the signature with the message.

        Parameters
        ----------
        message : str or bytes
            message that is to be verified.
        sign : bytes
            Base 64 encoded signature.
        *args : optional

        Returns
        -------
        bool
            True if verified, False if not.

        '''
        sign = base64.b64decode(sign)
        if not isinstance(message, bytes):
            message = message.encode()
        key = self.public_RSA
        if len(args) == 1:
            key = self.return_public_key_object(args[0])
        try:
            x = rsa.verify(message, sign, key)
            if x == 'SHA-256':
                return True
            else:
                return False
        except Exception as e:
            print('Exception in Encrypt.RSA_verify',e)
            return False
        
    def encrypt(self, message, key):
        ''' Encrypts the message with given PEM format public key.

        Parameters
        ----------
        message : str or bytes
            message that is to be encrypted.
        key : str or bytes
            PEM format public key.

        Returns
        -------
        encrypted_key : bytes
            base 64 encoded encrypted AES key.
        encrypted_message : bytes
            encrypted message.
        key : str or bytes
            PEM format public key.

        '''
        try:
            # pub_key = self.return_public_key_object(key)
            if not isinstance(key, bytes):
                key = key.encode()
            AES_key = Random.new().read(30)
            A = AESCipher(AES_key)
            encrypted_message = A.encrypt(message)
            encrypted_key = self.RSA_encrypt(AES_key, key)
            encrypted_key = base64.b64encode(encrypted_key)            
            return (encrypted_key, encrypted_message, key)
        except Exception as e:
            print('Exception in Encrypt.encrypt', e)
    
    def decrypt(self, encrypted_message, encrypted_key):
        '''

        Parameters
        ----------
        encrypted_message : bytes
            encrypted message.
        encrypted_key : 
            base 64 encoded encrypted AES key.

        Returns
        -------
        message : bytes
            decrypted message.

        '''
        try:
            encrypted_key = base64.b64decode(encrypted_key)
            AES_key = self.RSA_decrypt(encrypted_key)
            A = AESCipher(AES_key)
            message = A.decrypt(encrypted_message)
            return message
        except Exception as e:
            print('Exception in Encrypt.decrypt',e)
            return None
        