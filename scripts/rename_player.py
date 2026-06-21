#!/usr/bin/env python3
"""
Unifica votos de un jugador en Firebase Realtime Database.

Uso:
  python rename_player.py "Irene Martinez" "Irene"

Requiere:
  pip install firebase-admin
  Variable de entorno FIREBASE_CREDENTIALS con la ruta al JSON de cuenta de servicio,
  o pasar --creds <ruta>.

Lo que hace:
  1. Para cada partido en votes/, busca la clave origen.
  2. Si la clave destino no existe aún, copia el voto con el nombre correcto.
  3. Si la clave destino ya existe, mantiene el destino (no lo sobreescribe).
  4. Borra la clave origen.
"""

import argparse
import os
import sys

try:
    import firebase_admin
    from firebase_admin import credentials, db
except ImportError:
    sys.exit("❌ Instala firebase-admin: pip install firebase-admin")


DATABASE_URL = "https://mundial-99cdc-default-rtdb.europe-west1.firebasedatabase.app"


def safe_key(name: str) -> str:
    """Mismo algoritmo que safeKey() en index.html."""
    for ch in ".#$/[]":
        name = name.replace(ch, "_")
    return name


def init_firebase(creds_path: str):
    cred = credentials.Certificate(creds_path)
    firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})


def rename_player(src_name: str, dst_name: str, dry_run: bool = False):
    src_key = safe_key(src_name)
    dst_key = safe_key(dst_name)

    if src_key == dst_key:
        print(f"⚠️  Las claves son idénticas ({src_key}), nada que hacer.")
        return

    votes_ref = db.reference("votes")
    all_votes = votes_ref.get() or {}

    moved = 0
    skipped = 0
    not_found = 0

    for match_id, players in all_votes.items():
        if not isinstance(players, dict):
            continue
        if src_key not in players:
            not_found += 1
            continue

        src_vote = players[src_key]
        has_dst = dst_key in players

        if has_dst:
            print(f"  [{match_id}] destino ya existe - se conserva el voto existente, se borra el origen")
            skipped += 1
        else:
            new_vote = dict(src_vote)
            new_vote["name"] = dst_name  # actualiza el nombre visible
            if dry_run:
                print(f"  [{match_id}] DRY-RUN: copiar {src_key} -> {dst_key}: {new_vote}")
            else:
                votes_ref.child(f"{match_id}/{dst_key}").set(new_vote)
            moved += 1

        if not dry_run:
            votes_ref.child(f"{match_id}/{src_key}").delete()

    print(f"\n{'DRY-RUN ' if dry_run else ''}Resultado:")
    print(f"  Votos migrados:          {moved}")
    print(f"  Destino ya existia:      {skipped}")
    print(f"  Partidos sin voto origen: {not_found}")
    print(f"  Total partidos revisados: {len(all_votes)}")


def main():
    parser = argparse.ArgumentParser(description="Unifica votos de jugador en Firebase.")
    parser.add_argument("src", help="Nombre origen (el que hay que eliminar)")
    parser.add_argument("dst", help="Nombre destino (el que hay que conservar)")
    parser.add_argument("--creds", default=os.environ.get("FIREBASE_CREDENTIALS", ""),
                        help="Ruta al JSON de cuenta de servicio (o env FIREBASE_CREDENTIALS)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Solo muestra lo que haría, sin modificar nada")
    args = parser.parse_args()

    if not args.creds:
        sys.exit("❌ Especifica la ruta al JSON de cuenta de servicio con --creds o FIREBASE_CREDENTIALS.")

    print(f"Renombrando '{args.src}' -> '{args.dst}'" + (" [DRY-RUN]" if args.dry_run else ""))
    init_firebase(args.creds)
    rename_player(args.src, args.dst, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
