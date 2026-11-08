// Muestra poco a poco los bloques marcados con «eco-aparecer» cuando entran en la pantalla y los vuelve
// a ocultar cuando salen, cada vez que se hace scroll hacia arriba o hacia abajo.
(function () {
    "use strict";

    var html = document.documentElement;
    var menosMovimiento = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!("IntersectionObserver" in window) || menosMovimiento) {
        // Navegador antiguo o la persona pidió menos movimiento: todo se ve normal, sin animación.
        return;
    }
    html.classList.add("eco-animado");

    // Se muestra cuando al menos el 10 % del bloque está en pantalla y se oculta cuando sale por completo.
    // Entre esos dos puntos se deja como está, para que no parpadee justo en el borde.
    var PARTE_PARA_MOSTRAR = 0.1;

    var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            var bloque = entrada.target;
            if (entrada.intersectionRatio >= PARTE_PARA_MOSTRAR) {
                bloque.classList.add("eco-visible");
            } else if (!entrada.isIntersecting) {
                bloque.classList.remove("eco-visible");
                // Salió por arriba de la pantalla: al volver, entra desde arriba.
                bloque.classList.toggle("eco-arriba", entrada.boundingClientRect.top < 0);
            }
        });
    }, { threshold: [0, PARTE_PARA_MOSTRAR] });

    document.querySelectorAll(".eco-aparecer").forEach(function (bloque) {
        observador.observe(bloque);
    });
})();
