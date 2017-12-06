#include "Bridge.h"
#include "Process.h"
#include "secrets.h"

const char* const PROGMEM CERTIFICATES_DEFAULT_PATH = "/usr/lib/python2.7/AWS-IoT-Python-Runtime/certs/";

#define AWS_IOT_CA_CERTIFICATE_SIZE 1758
#define THING_CERTIFICATE_SIZE 1220
#define THING_KEY_SIZE 1679

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while (!Serial) {}
  Serial.println(F("This sketch configures the certificates for AWS IoT SDK"));
  Serial.println(F("Make sure your Yun is running at least 17.11 image"));

  Serial.println(F("Starting Bridge"));
  //Bridge.begin();

  //installPackages();

  Serial.println(F("Uploading certificates from secrets.h"));
  Bridge.end();

  const __FlashStringHelper* AWS_IOT_CA_CERTIFICATE = F(SECRET_AWS_IOT_CA_CERTIFICATE);
  const __FlashStringHelper* THING_CERTIFICATE =  F(SECRET_THING_CERTIFICATE);
  const __FlashStringHelper* THING_KEY = F(SECRET_THING_KEY);

  uploadCertificate((const char*)AWS_IOT_CA_CERTIFICATE, AWS_IOT_CA_CERTIFICATE_SIZE, "aws-iot-rootCA.crt");
  uploadCertificate((const char*)THING_CERTIFICATE, THING_CERTIFICATE_SIZE, "myYun.cert.pem");
  uploadCertificate((const char*)THING_KEY, THING_KEY_SIZE, "myYun.private.key");

  Serial.println(F("All done! Now you can use any other example without further configuration"));
  delay(1000);
}

#if 0
void uploadCertificate(const char* const PROGMEM certificate, const char* filename) {
  Process upload;
  int exitCode ;
  upload.begin(F("echo "));
  upload.addParameter(certificate);
  upload.addParameter(F(" > "));
  upload.addParameter(String(CERTIFICATES_DEFAULT_PATH) + filename);
  upload.run();
  while (upload.available() > 0) {
    char c = upload.read();
    Serial.print(c);
  }
  // Ensure the last bit of data is sent.
  Serial.flush();
}

#else

int find_header(const char* const PROGMEM certificate, int cert_size) {
  int index = 0;
  int count = 0;
  for (int i = 0; i < cert_size; i++) {
    if (pgm_read_byte(&certificate[i]) == '-') {
      count++;
    }
    if (count == 10) {
      return i + 1;
    }
  }
  return -1;
}

int find_footer(const char* const PROGMEM certificate, int cert_size) {
  int index = 0;
  int count = 0;
  for (int i = 0; i < cert_size; i++) {
    if (pgm_read_byte(&certificate[i]) == '-') {
      count++;
    }
    if (count == 11) {
      return i;
    }
  }
  return -1;
}

inline void uploadCertificate(const char* const PROGMEM certificate, int cert_size, const char* filename) {

  char buffer[64];

  Serial1.print("rm ");
  Serial1.print(CERTIFICATES_DEFAULT_PATH);
  Serial1.println(filename);

  int header_end = find_header(certificate, cert_size);
  int footer_begin = find_footer(certificate, cert_size);

  for (int i = 0; i < header_end; i++) {
    buffer[i] = pgm_read_byte(&certificate[i]);
  }
  Serial1.print(F("cat << EOF >> "));
  Serial1.print(CERTIFICATES_DEFAULT_PATH);
  Serial1.print(filename);
  Serial1.print('\n');
  Serial1.write(buffer, header_end);
  Serial1.println(F("\nEOF"));

  bool end_reached = false;

  for (int i = header_end; i < footer_begin && end_reached == false; i = i + 64) {
    int size = 64;
    for (int j = 0; j < 64; j++) {
      if (i + j < footer_begin) {
        buffer[j] = pgm_read_byte(&certificate[i + j]);
      } else {
        size = j + 1;
        buffer[j] = '\0';
        end_reached = true;
        break;
      }
    }

    if (end_reached) {
      Serial.print("Last line is ");
      Serial.write(buffer, size);
    }

    Serial1.print(F("cat << EOF >> "));
    Serial1.print(CERTIFICATES_DEFAULT_PATH);
    Serial1.print(filename);
    Serial1.print('\n');
    Serial1.write(buffer, size);
    Serial1.println(F("\nEOF"));
  }

  int count = 0;
  int size = 0;
  for (int i = 0; i < (cert_size - footer_begin); i++) {
    buffer[i] = pgm_read_byte(&certificate[i + footer_begin]);
    if (buffer[i] == '-') {
      count ++;
    }
    if (count == 10) {
      size = i + 1;
      break;
    }
  }

  Serial.println("Footer is ");
  Serial.write(buffer, size);

  Serial1.print(F("cat << EOF >> "));
  Serial1.print(CERTIFICATES_DEFAULT_PATH);
  Serial1.print(filename);
  Serial1.print('\n');
  Serial1.write(buffer, size);
  Serial1.println(F("\nEOF"));
}
#endif

void installPackages() {
  Serial.println(F("Installing packages"));
  Process install;
  int exitCode = install.runShellCommand(F("opkg update && opkg install aws-iot-device-sdk aws-iot-runtime-yun"));
  if (exitCode != 0) {
    Serial.println(F("Packages installation failed"));
    halt();
  }
}

void loop() {
  return;
  // This turns the sketch into a YunSerialTerminal
  if (Serial.available()) {
    char c = (char)Serial.read();
    Serial1.write(c);
  }
  if (Serial1.available()) {
    char c = (char)Serial1.read();
    Serial.write(c);
  }
}

void halt() {
  Serial.flush();
  Bridge.end();
  while (true) {
    loop();
  }
}
