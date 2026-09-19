"""Genera la distribucion normal de todas las mediciones como una sola muestra."""
from csv import reader
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parents[1]
DATOS = BASE / "datos"
SALIDA = BASE / "imagenes" / "distribuciones_muestra.png"


def leer_csv(ruta: Path) -> np.ndarray:
    """Lee un archivo CSV de una sola columna con valores en milimetros."""
    with ruta.open(newline="", encoding="utf-8") as archivo:
        return np.array([float(fila[0]) for fila in reader(archivo) if fila], dtype=float)


def leer_muestras_por_persona() -> dict[str, np.ndarray]:
    """Lee las mediciones y las agrupa por el nombre del observador."""
    archivos = sorted(DATOS.glob("datos-*.csv"))
    if not archivos:
        raise FileNotFoundError("No se encontraron archivos CSV en la carpeta datos")
    muestras = {"Carlos": [], "Angelo": []}
    for archivo in archivos:
        nombre = archivo.stem.split("-")[-1].lower()
        persona = "Carlos" if nombre == "carlos" else "Angelo"
        muestras[persona].append(leer_csv(archivo))
    return {persona: np.concatenate(lecturas) for persona, lecturas in muestras.items()}


def densidad_normal(eje: np.ndarray, media: float, desviacion: float) -> np.ndarray:
    """Calcula la densidad normal estimada con media y s muestral."""
    return np.exp(-0.5 * ((eje - media) / desviacion) ** 2) / (desviacion * np.sqrt(2 * np.pi))


def main() -> None:
    muestras = leer_muestras_por_persona()
    datos = np.concatenate(list(muestras.values()))
    media = float(np.mean(datos))
    desviacion = float(np.std(datos, ddof=1))
    limite_inferior = media - 2 * desviacion
    limite_superior = media + 2 * desviacion
    eje = np.linspace(datos.min() - 0.12, datos.max() + 0.12, 700)
    curva = densidad_normal(eje, media, desviacion)
    valores, frecuencias = np.unique(datos, return_counts=True)
    escala_curva = curva / curva.max() * frecuencias.max() * 0.85

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(eje, escala_curva, color="#176b87", linewidth=2.4, label="Normal estimada")
    colores = {"Carlos": "#d95f02", "Angelo": "#178719"}
    etiquetas_grafica = set()
    for valor, frecuencia in zip(valores, frecuencias):
        nivel = 0
        for persona, muestras_persona in muestras.items():
            cantidad = int(np.count_nonzero(muestras_persona == valor))
            if cantidad == 0:
                continue
            ax.scatter(
                np.full(cantidad, valor),
                np.arange(nivel + 1, nivel + cantidad + 1),
                marker="+",
                s=70,
                linewidths=1.5,
                color=colores[persona],
                label=persona if persona not in etiquetas_grafica else None,
                zorder=3,
            )
            etiquetas_grafica.add(persona)
            nivel += cantidad
        ax.annotate(
            f"{frecuencia}",
            (valor, frecuencia),
            xytext=(0, 5),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    ax.axvline(media, color="#222222", linewidth=1.5, label=f"Media = {media:.4f} mm")
    ax.axvline(
        limite_inferior,
        color="#555555",
        linestyle="--",
        linewidth=1.2,
        label=r"Limites $\bar{x}\pm2s$",
    )
    ax.axvline(limite_superior, color="#555555", linestyle="--", linewidth=1.2)
    ax.axvspan(limite_inferior, limite_superior, color="#176b87", alpha=0.08)
    ax.set_title("Distribucion normal del diametro: muestra completa")
    ax.set_xlabel("Diametro (mm)")
    ax.set_ylabel("Frecuencia de las lecturas")
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left")
    fig.tight_layout()

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SALIDA, dpi=220, bbox_inches="tight")
    print(f"n={len(datos)}")
    print(f"media={media:.6f} mm")
    print(f"s={desviacion:.6f} mm")
    print(f"2s={2 * desviacion:.6f} mm")
    print("frecuencias=" + ", ".join(f"{valor:.2f} mm: {frecuencia}" for valor, frecuencia in zip(valores, frecuencias)))
    for persona, muestras_persona in muestras.items():
        print(f"{persona}: {len(muestras_persona)} mediciones")
    print(f"Grafica guardada en: {SALIDA}")


if __name__ == "__main__":
    main()
