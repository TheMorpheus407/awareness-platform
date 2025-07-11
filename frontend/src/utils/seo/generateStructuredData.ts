export const generateCourseStructuredData = (course: {
  name: string;
  description: string;
  provider: string;
  url: string;
  price?: number;
  currency?: string;
  duration?: string;
  language?: string;
}) => {
  return {
    "@context": "https://schema.org",
    "@type": "Course",
    "name": course.name,
    "description": course.description,
    "provider": {
      "@type": "Organization",
      "name": course.provider,
      "sameAs": "https://awareness.bootstrapacademy.com"
    },
    "url": course.url,
    "hasCourseInstance": {
      "@type": "CourseInstance",
      "courseMode": "online",
      "duration": course.duration || "PT1H",
      "inLanguage": course.language || "en"
    },
    ...(course.price && {
      "offers": {
        "@type": "Offer",
        "price": course.price,
        "priceCurrency": course.currency || "EUR",
        "availability": "https://schema.org/InStock"
      }
    })
  };
};

export const generateFAQStructuredData = (faqs: Array<{ question: string; answer: string }>) => {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": faqs.map(faq => ({
      "@type": "Question",
      "name": faq.question,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": faq.answer
      }
    }))
  };
};

export const generateBreadcrumbStructuredData = (items: Array<{ name: string; url: string }>) => {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": items.map((item, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "name": item.name,
      "item": item.url
    }))
  };
};

export const generateProductStructuredData = (product: {
  name: string;
  description: string;
  image: string;
  price: number;
  currency: string;
  ratingValue?: number;
  reviewCount?: number;
}) => {
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": product.name,
    "description": product.description,
    "image": product.image,
    "brand": {
      "@type": "Brand",
      "name": "Bootstrap Academy"
    },
    "offers": {
      "@type": "Offer",
      "url": "https://awareness.bootstrapacademy.com/pricing",
      "priceCurrency": product.currency,
      "price": product.price,
      "availability": "https://schema.org/InStock"
    },
    ...(product.ratingValue && product.reviewCount && {
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": product.ratingValue,
        "reviewCount": product.reviewCount
      }
    })
  };
};

export const generateEventStructuredData = (event: {
  name: string;
  description: string;
  startDate: string;
  endDate: string;
  location?: string;
  isOnline: boolean;
  url: string;
  price?: number;
  currency?: string;
}) => {
  return {
    "@context": "https://schema.org",
    "@type": "Event",
    "name": event.name,
    "description": event.description,
    "startDate": event.startDate,
    "endDate": event.endDate,
    "eventAttendanceMode": event.isOnline ? "https://schema.org/OnlineEventAttendanceMode" : "https://schema.org/OfflineEventAttendanceMode",
    "eventStatus": "https://schema.org/EventScheduled",
    "location": event.isOnline ? {
      "@type": "VirtualLocation",
      "url": event.url
    } : {
      "@type": "Place",
      "name": event.location,
      "address": event.location
    },
    "organizer": {
      "@type": "Organization",
      "name": "Bootstrap Academy",
      "url": "https://awareness.bootstrapacademy.com"
    },
    ...(event.price && {
      "offers": {
        "@type": "Offer",
        "price": event.price,
        "priceCurrency": event.currency || "EUR",
        "availability": "https://schema.org/InStock",
        "url": event.url
      }
    })
  };
};