#!/usr/bin/env python3
"""
Baca data ADC dari STM32 (USB CDC Virtual COM Port) dan simpan ke file CSV.
Jalankan di Raspberry Pi.

Pemakaian:
    python3 raspi_serial_logger.py
    python3 raspi_serial_logger.py --port /dev/ttyACM0 --baud 115200 --out data.csv
"""

import argparse
import csv
import datetime
import sys

import serial


def parse_args():
    parser = argparse.ArgumentParser(description="Log data ADC dari STM32 via USB CDC ke CSV")
    parser.add_argument("--port", default="/dev/ttyACM0", help="Path serial port (default: /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baudrate (diabaikan USB CDC, default: 115200)")
    parser.add_argument("--out", default=None, help="Nama file CSV output (default: auto timestamp)")
    parser.add_argument("--prefix", default=">ADC:", help="Prefix baris data yang diparsing (default: '>ADC:')")
    return parser.parse_args()


def main():
    args = parse_args()

    out_path = args.out
    if out_path is None:
        out_path = datetime.datetime.now().strftime("adc_log_%Y%m%d_%H%M%S.csv")

    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except serial.SerialException as e:
        print(f"Gagal membuka {args.port}: {e}", file=sys.stderr)
        sys.exit(1)

    sample_count = 0

    print(f"Membaca dari {args.port}, menyimpan ke {out_path}")
    print("Tekan Ctrl+C untuk berhenti.")

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "sample_index", "adc_value"])

        try:
            while True:
                raw = ser.readline()
                if not raw:
                    continue  # timeout, tidak ada data baru

                line = raw.decode("utf-8", errors="ignore").strip()
                if not line.startswith(args.prefix):
                    continue

                value_str = line[len(args.prefix):]
                try:
                    value = int(value_str)
                except ValueError:
                    continue  # baris rusak/terpotong, lewati

                timestamp = datetime.datetime.now().isoformat(timespec="milliseconds")
                writer.writerow([timestamp, sample_count, value])
                sample_count += 1

                if sample_count % 10 == 0:
                    f.flush()
                    print(f"\r{sample_count} sampel tersimpan", end="", flush=True)

        except KeyboardInterrupt:
            print(f"\nDihentikan oleh user. Total {sample_count} sampel tersimpan di {out_path}")
        finally:
            f.flush()
            ser.close()


if __name__ == "__main__":
    main()
