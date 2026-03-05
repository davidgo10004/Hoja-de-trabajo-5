import random
import simpy
import statistics
import csv
import os
import matplotlib.pyplot as plt


RANDOM_SEED = 42
PROCESOS_LISTA = [25, 50, 100, 150, 200]
INTERVALOS = [10, 5, 1]
IO_TIME = 1  



def proceso(env, pid, ram, cpu, tiempos, instrucciones_por_turno):
    llegada = env.now
    memoria = random.randint(1, 10)
    instrucciones = random.randint(1, 10)

   
    yield ram.get(memoria)

   
    while instrucciones > 0:
        
        with cpu.request() as req:
            yield req

            
            ejecutar = min(instrucciones_por_turno, instrucciones)
            yield env.timeout(1)
            instrucciones -= ejecutar

       
        if instrucciones > 0:
            numero = random.randint(1, 21)
            if numero == 1:
              
                yield env.timeout(IO_TIME)

   
    yield ram.put(memoria)

    salida = env.now
    tiempos.append(salida - llegada)



def generar_procesos(env, ram, cpu, tiempos, cantidad_procesos, instrucciones_por_turno, intervalo):
    for i in range(cantidad_procesos):
        
        yield env.timeout(random.expovariate(1.0 / intervalo))
        env.process(proceso(env, i + 1, ram, cpu, tiempos, instrucciones_por_turno))



def correr_simulacion(cantidad_procesos, intervalo, ram_total, cpu_count, instrucciones_por_turno, seed):
    random.seed(seed)

    env = simpy.Environment()
    ram = simpy.Container(env, init=ram_total, capacity=ram_total)
    cpu = simpy.Resource(env, capacity=cpu_count)
    tiempos = []

    env.process(generar_procesos(env, ram, cpu, tiempos, cantidad_procesos, instrucciones_por_turno, intervalo))
    env.run()

    promedio = statistics.mean(tiempos) if tiempos else 0.0
    desviacion = statistics.stdev(tiempos) if len(tiempos) > 1 else 0.0
    return promedio, desviacion



def ejecutar_estrategia(nombre, ram_total, cpu_count, instrucciones_por_turno, out_dir="resultados"):
    os.makedirs(out_dir, exist_ok=True)

    resultados = []  

    for intervalo in INTERVALOS:
        promedios = []
        desvios = []

        for n in PROCESOS_LISTA:
          
            seed = RANDOM_SEED + intervalo * 1000 + n

            prom, std = correr_simulacion(
                cantidad_procesos=n,
                intervalo=intervalo,
                ram_total=ram_total,
                cpu_count=cpu_count,
                instrucciones_por_turno=instrucciones_por_turno,
                seed=seed
            )

            promedios.append(prom)
            desvios.append(std)

            resultados.append({
                "estrategia": nombre,
                "intervalo": intervalo,
                "procesos": n,
                "ram": ram_total,
                "cpus": cpu_count,
                "quantum_instr": instrucciones_por_turno,
                "promedio": prom,
                "desviacion": std
            })

            print(f"[{nombre}] Intervalo={intervalo} N={n} -> prom={prom:.2f} std={std:.2f}")

       
        plt.figure()
        plt.plot(PROCESOS_LISTA, promedios)
        plt.xlabel("Número de procesos")
        plt.ylabel("Tiempo promedio")
        plt.title(f"{nombre} | Intervalo {intervalo}")
        filename = f"{nombre.replace(' ', '_')}_intervalo_{intervalo}.png"
        plt.savefig(os.path.join(out_dir, filename), dpi=200, bbox_inches="tight")
        plt.close()

    return resultados


def guardar_csv(resultados, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=resultados[0].keys())
        writer.writeheader()
        writer.writerows(resultados)


if __name__ == "__main__":
  
    estrategias = [
        ("A_RAM_200", 200, 1, 3),   # a) RAM 200
        ("B_CPU_rapido_Q6", 100, 1, 6),  # b) CPU rápido
        ("C_2_CPUs", 100, 2, 3)     # c) 2 CPUs
    ]

    all_results = []
    for nombre, ram_total, cpu_count, q in estrategias:
        all_results.extend(ejecutar_estrategia(nombre, ram_total, cpu_count, q, out_dir="resultados"))

    guardar_csv(all_results, os.path.join("resultados", "resumen_resultados.csv"))

    print("\n Listo. Se generaron 9 gráficas PNG en la carpeta 'resultados' y un CSV con los datos.")