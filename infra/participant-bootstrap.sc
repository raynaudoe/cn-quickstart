def main(): Unit = {
  application.health.wait_for_initialized()
  application.synchronizers.connect("global", "http://canton:5008")
  utils.retry_until_true { application.synchronizers.active("global") }
  java.nio.file.Files.writeString(java.nio.file.Path.of("/tmp/participant-ready"), "ready")
}
