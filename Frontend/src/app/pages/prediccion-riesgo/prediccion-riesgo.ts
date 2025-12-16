import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-prediccion-riesgo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './prediccion-riesgo.html',
  styleUrl: './prediccion-riesgo.css'
})
export class PrediccionRiesgo {
  // Estado para controlar la visibilidad de los resultados
  showPredictionResult = true; // Mostrar 'Ingrese los datos...'
  showRiskDisplay = false;     // Ocultar 'RIESGO ALTO/BAJO'

  // Propiedades para enlazar el resultado de la predicción
  riskIconClass: string = '';
  riskTextClass: string = '';
  riskTextContent: string = '';
  riskDetailContent: string = '';
  riskCardClass: string = 'border-accent-cyan'; // Clase inicial del borde

  // Referencia al elemento de la tarjeta para manipular su clase CSS
  @ViewChild('riskCard') riskCard!: ElementRef;

  // Lógica de simulación de predicción
  onPredictRisk() {
    // 1. Simular la predicción (50% de probabilidad de ser alto riesgo)
    const isHighRisk = Math.random() < 0.5;

    // 2. Ocultar el mensaje de inicio y mostrar el resultado
    this.showPredictionResult = false;
    this.showRiskDisplay = true;

    // 3. Establecer las clases y contenidos
    if (isHighRisk) {
      // Alto Riesgo (Estilo Peligro - Rojo)
      this.riskIconClass = 'fas fa-thumbs-down text-8xl mb-4 text-red-500';
      this.riskTextClass = 'text-2xl font-extrabold text-red-400';
      this.riskTextContent = 'RIESGO ALTO';
      this.riskDetailContent = 'El modelo predice una alta probabilidad de deserción o bajo rendimiento.';
      this.riskCardClass = 'border-red-500'; // Borde rojo
    } else {
      // Bajo Riesgo (Estilo Éxito - Verde)
      this.riskIconClass = 'fas fa-thumbs-up text-8xl mb-4 text-green-500';
      this.riskTextClass = 'text-2xl font-extrabold text-green-400';
      this.riskTextContent = 'RIESGO BAJO';
      this.riskDetailContent = 'El rendimiento del estudiante se proyecta como óptimo.';
      this.riskCardClass = 'border-accent-cyan'; // Borde cian
    }
  }
}