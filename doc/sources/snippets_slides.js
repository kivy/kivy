let currentSlide = 0;

document
  .querySelector('.carousel-container')
  ?.addEventListener("click", (e) => {
    const link = e.target.closest("a");
    if (!link) return;

    const href = link.getAttribute("href");
    if (!href) return;

    const isImage = /\.(png|jpeg|jpg|gif|svg|webp)(\?.*)?$/i.test(href);
    const isExternal = href.startsWith("http://") || href.startsWith("https://");

    if (isImage || isExternal) {
      e.preventDefault();
      globalThis.open(href, "_blank", "noopener,noreferrer");
    }
  });

async function loadSlideContent(slide) {
  if (!slide || slide.dataset.loaded === "true") return;

  const src = slide.getAttribute("data-src");
  const container = slide.querySelector(".rst-content");

  try {
    const response = await fetch(src);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const htmlText = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, "text/html");
    const content = doc.querySelector('[role="main"]');

    content.querySelectorAll("[src]").forEach((element) => {
      element.src = new URL(
        element.getAttribute("src"),
        response.url,
      ).href;
    });

    content.querySelectorAll("[href]").forEach((element) => {
      const href = element.getAttribute("href");

      if (href && !href.startsWith("#")) {
        element.href = new URL(href, response.url).href;
      }
    });

    container.innerHTML = content.innerHTML;
    slide.dataset.loaded = "true";
  } catch (error) {
    container.innerHTML = `<p>Error loading content from ${src}</p>`;
    console.error(error);
  }
}

function unloadSlideContent(slide) {
  if (!slide || slide.dataset.loaded !== "true") return;

  const container = slide.querySelector(".rst-content");
  if (container) {
    container.innerHTML = "Loading...";
  }
  delete slide.dataset.loaded;
}

function showSlide(index) {
  const slides = document.querySelectorAll(".carousel-slide");
  if (!slides.length) return;

  const newIndex = (index + slides.length) % slides.length;

  // 1. Unload the previous slide
  if (slides[currentSlide] && currentSlide !== newIndex) {
    unloadSlideContent(slides[currentSlide]);
  }

  currentSlide = newIndex;

  const track = document.querySelector(".carousel-track");
  if (track) {
    track.style.transform = `translateX(-${currentSlide * 100}%)`;
  }

  loadSlideContent(slides[currentSlide]);
}

// deno-lint-ignore no-unused-vars
function moveSlide(direction) {
  showSlide(currentSlide + direction);
}

document.addEventListener("DOMContentLoaded", () => {
  showSlide(0);
});
