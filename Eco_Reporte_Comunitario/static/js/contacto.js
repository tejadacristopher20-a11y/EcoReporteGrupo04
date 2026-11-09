// Panel de contacto: el botón «Contacto» de la barra verde lo abre y lo cierra.
// Aparece en la parte baja de la pantalla, donde esté la persona. Si se ve el pie de página, el panel queda por
// detrás de él y sus datos se acomodan justo encima, sin que el pie los tape.
(function () {
    "use strict";

    var boton = document.getElementById("eco-boton-contacto");
    var panel = document.getElementById("eco-contacto");
    if (!boton || !panel) {
        return;
    }
    var cerrar = panel.querySelector(".eco-contacto-cerrar");
    var pie = document.querySelector(".eco-footer");
    var raiz = document.documentElement;
    var pendiente = false;
    var pendienteTamano = false;

    function estaAbierto() {
        return panel.classList.contains("eco-abierto");
    }

    // Cuánto del pie de página se ve en la parte baja de la pantalla (0 si todavía no se llega al final).
    function acomodarSobreElPie() {
        pendiente = false;
        var visible = 0;
        if (pie) {
            visible = Math.min(Math.max(0, window.innerHeight - pie.getBoundingClientRect().top), pie.offsetHeight);
        }
        panel.style.setProperty("--eco-pie-visible", Math.round(visible) + "px");
    }

    // Espacio al final de la página igual a la parte del panel que queda sobre el contenido: así, al bajar
    // hasta el final, las últimas tarjetas quedan por encima del panel y no debajo de él.
    function reservarEspacio() {
        pendienteTamano = false;
        var partePie = parseFloat(panel.style.getPropertyValue("--eco-pie-visible")) || 0;
        raiz.style.setProperty("--eco-alto-contacto", Math.max(0, Math.round(panel.offsetHeight - partePie)) + "px");
    }

    // Al hacer scroll, se recalcula como máximo una vez por cuadro.
    function alMoverse() {
        if (!pendiente) {
            pendiente = true;
            window.requestAnimationFrame(acomodarSobreElPie);
        }
    }

    // Al cambiar el tamaño de la pantalla (o girar el celular), el panel puede cambiar de alto.
    function alCambiarTamano() {
        if (!pendienteTamano) {
            pendienteTamano = true;
            window.requestAnimationFrame(function () {
                acomodarSobreElPie();
                reservarEspacio();
            });
        }
    }

    function abrir() {
        acomodarSobreElPie();
        reservarEspacio();
        document.body.classList.add("eco-contacto-abierto");
        panel.classList.add("eco-abierto");
        panel.setAttribute("aria-hidden", "false");
        boton.setAttribute("aria-expanded", "true");
        window.addEventListener("scroll", alMoverse, { passive: true });
        window.addEventListener("resize", alCambiarTamano);
        if (cerrar) {
            cerrar.focus({ preventScroll: true });
        }
    }

    function cerrarPanel(devolverFoco) {
        panel.classList.remove("eco-abierto");
        document.body.classList.remove("eco-contacto-abierto");
        panel.setAttribute("aria-hidden", "true");
        boton.setAttribute("aria-expanded", "false");
        window.removeEventListener("scroll", alMoverse);
        window.removeEventListener("resize", alCambiarTamano);
        if (devolverFoco) {
            boton.focus({ preventScroll: true });
        }
    }

    boton.addEventListener("click", function () {
        if (estaAbierto()) {
            cerrarPanel(true);
        } else {
            abrir();
        }
    });

    if (cerrar) {
        cerrar.addEventListener("click", function () {
            cerrarPanel(true);
        });
    }

    // La tecla Escape también lo cierra.
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape" && estaAbierto()) {
            cerrarPanel(true);
        }
    });
})();
