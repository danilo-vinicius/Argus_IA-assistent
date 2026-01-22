import sounddevice as sd

print("🎧 Listando dispositivos de áudio detectados:\n")
print(sd.query_devices())

print("\n🔊 Dispositivo Padrão Atual:")
print(sd.default.device)