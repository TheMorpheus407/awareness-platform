import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const Terms = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center space-x-2">
              <Shield className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Bootstrap Academy</span>
            </Link>
            <div className="flex items-center space-x-6">
              <LanguageSwitcher />
              <Link to="/" className="text-gray-600 hover:text-gray-900 transition-colors">
                {t('common.backToHome')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-8">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('common.back')}
          </Link>

          <h1 className="text-4xl font-bold text-gray-900 mb-8">{t('terms.title', 'Allgemeine Geschäftsbedingungen')}</h1>

          <div className="prose prose-lg max-w-none text-gray-700">
            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 1 Geltungsbereich</h2>
              <p className="mb-4">
                (1) Diese Allgemeinen Geschäftsbedingungen (nachfolgend "AGB") gelten für alle Geschäftsbeziehungen zwischen der 
                Bootstrap Academy GmbH (nachfolgend "Bootstrap Academy", "wir" oder "uns") und unseren Kunden (nachfolgend "Kunde" 
                oder "Sie") über unsere Plattform für Cybersecurity-Awareness-Schulungen.
              </p>
              <p className="mb-4">
                (2) Unsere Leistungen richten sich ausschließlich an Unternehmer im Sinne von § 14 BGB. Ein Vertragsschluss mit 
                Verbrauchern ist ausgeschlossen.
              </p>
              <p className="mb-4">
                (3) Abweichende, entgegenstehende oder ergänzende Allgemeine Geschäftsbedingungen des Kunden werden nur dann und 
                insoweit Vertragsbestandteil, als wir ihrer Geltung ausdrücklich schriftlich zugestimmt haben.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 2 Vertragsgegenstand</h2>
              <p className="mb-4">
                (1) Bootstrap Academy bietet eine cloudbasierte Plattform für Cybersecurity-Awareness-Schulungen, einschließlich:
              </p>
              <ul className="list-disc list-inside mb-4">
                <li>Phishing-Simulationen</li>
                <li>E-Learning-Module zur Cybersicherheit</li>
                <li>Analyse- und Reporting-Tools</li>
                <li>Compliance-Management-Funktionen</li>
              </ul>
              <p className="mb-4">
                (2) Der genaue Umfang der Leistungen ergibt sich aus der jeweiligen Leistungsbeschreibung und dem gewählten 
                Leistungspaket.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 3 Vertragsschluss</h2>
              <p className="mb-4">
                (1) Die Präsentation unserer Leistungen auf der Website stellt kein bindendes Angebot unsererseits dar, sondern 
                eine Aufforderung an den Kunden, ein Angebot abzugeben.
              </p>
              <p className="mb-4">
                (2) Durch Absenden der Bestellung über unser Online-Formular gibt der Kunde ein verbindliches Angebot zum Abschluss 
                eines Vertrages ab.
              </p>
              <p className="mb-4">
                (3) Wir können das Angebot des Kunden innerhalb von fünf Werktagen annehmen durch:
              </p>
              <ul className="list-disc list-inside mb-4">
                <li>Zusendung einer Auftragsbestätigung per E-Mail oder</li>
                <li>Freischaltung des Zugangs zur Plattform</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 4 Leistungsumfang und Durchführung</h2>
              <p className="mb-4">
                (1) Bootstrap Academy stellt dem Kunden die gebuchten Leistungen über die Plattform zur Verfügung. Die 
                Verfügbarkeit der Plattform beträgt im Jahresmittel mindestens 99%.
              </p>
              <p className="mb-4">
                (2) Der Kunde erhält Zugangsdaten, die es ihm ermöglichen, die Plattform zu nutzen und Mitarbeiter für Schulungen 
                zu registrieren.
              </p>
              <p className="mb-4">
                (3) Bootstrap Academy ist berechtigt, die Leistungen zu erweitern, zu ändern und Verbesserungen vorzunehmen, 
                insbesondere wenn diese dem technischen Fortschritt dienen, notwendig erscheinen, um Missbrauch zu verhindern, 
                oder Bootstrap Academy aufgrund gesetzlicher Vorschriften dazu verpflichtet ist.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 5 Pflichten des Kunden</h2>
              <p className="mb-4">
                (1) Der Kunde ist verpflichtet:
              </p>
              <ul className="list-disc list-inside mb-4">
                <li>Die Zugangsdaten vertraulich zu behandeln und vor unbefugtem Zugriff zu schützen</li>
                <li>Die Plattform nur für die vertraglich vereinbarten Zwecke zu nutzen</li>
                <li>Keine rechtswidrigen Inhalte über die Plattform zu verbreiten</li>
                <li>Die geltenden Datenschutzbestimmungen einzuhalten</li>
              </ul>
              <p className="mb-4">
                (2) Der Kunde stellt sicher, dass die Nutzung der Phishing-Simulationen im Einklang mit den geltenden 
                arbeitsrechtlichen und datenschutzrechtlichen Bestimmungen erfolgt.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 6 Preise und Zahlungsbedingungen</h2>
              <p className="mb-4">
                (1) Es gelten die zum Zeitpunkt der Bestellung angegebenen Preise. Alle Preise verstehen sich zuzüglich der 
                gesetzlichen Umsatzsteuer.
              </p>
              <p className="mb-4">
                (2) Die Abrechnung erfolgt wahlweise monatlich oder jährlich im Voraus. Bei jährlicher Zahlung gewähren wir einen 
                Rabatt gemäß der aktuellen Preisliste.
              </p>
              <p className="mb-4">
                (3) Rechnungen sind innerhalb von 14 Tagen nach Erhalt ohne Abzug zur Zahlung fällig.
              </p>
              <p className="mb-4">
                (4) Bei Zahlungsverzug sind wir berechtigt, Verzugszinsen in Höhe von 9 Prozentpunkten über dem Basiszinssatz zu 
                berechnen.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 7 Laufzeit und Kündigung</h2>
              <p className="mb-4">
                (1) Der Vertrag hat eine Mindestlaufzeit entsprechend dem gewählten Abrechnungszeitraum (monatlich oder jährlich).
              </p>
              <p className="mb-4">
                (2) Der Vertrag verlängert sich automatisch um den gleichen Zeitraum, wenn er nicht mit einer Frist von einem Monat 
                zum Ende der jeweiligen Laufzeit gekündigt wird.
              </p>
              <p className="mb-4">
                (3) Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt.
              </p>
              <p className="mb-4">
                (4) Kündigungen bedürfen der Textform (E-Mail genügt).
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 8 Gewährleistung und Haftung</h2>
              <p className="mb-4">
                (1) Bootstrap Academy haftet unbeschränkt für Vorsatz und grobe Fahrlässigkeit sowie nach Maßgabe des 
                Produkthaftungsgesetzes. Für leichte Fahrlässigkeit haftet Bootstrap Academy nur bei Verletzung einer wesentlichen 
                Vertragspflicht (Kardinalpflicht), deren Erfüllung die ordnungsgemäße Durchführung des Vertrags überhaupt erst 
                ermöglicht und auf deren Einhaltung der Kunde regelmäßig vertrauen darf.
              </p>
              <p className="mb-4">
                (2) Die Haftung für leichte Fahrlässigkeit ist der Höhe nach beschränkt auf die bei Vertragsschluss vorhersehbaren 
                Schäden, mit deren Entstehung typischerweise gerechnet werden muss.
              </p>
              <p className="mb-4">
                (3) Die vorstehenden Haftungsbeschränkungen gelten nicht bei Verletzung von Leben, Körper und Gesundheit.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 9 Datenschutz</h2>
              <p className="mb-4">
                (1) Die Vertragsparteien werden die jeweils anwendbaren datenschutzrechtlichen Bestimmungen beachten.
              </p>
              <p className="mb-4">
                (2) Bootstrap Academy verarbeitet personenbezogene Daten im Auftrag des Kunden. Die Einzelheiten regelt eine 
                gesonderte Vereinbarung zur Auftragsverarbeitung.
              </p>
              <p className="mb-4">
                (3) Der Kunde bleibt sowohl allgemein im Auftragsverhältnis als auch im datenschutzrechtlichen Sinne "Herr der 
                Daten".
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 10 Vertraulichkeit</h2>
              <p className="mb-4">
                (1) Die Vertragsparteien verpflichten sich, alle im Rahmen der Vertragsanbahnung und -durchführung erlangten 
                vertraulichen Informationen der jeweils anderen Partei zeitlich unbegrenzt vertraulich zu behandeln und nur für 
                Vertragszwecke zu verwenden.
              </p>
              <p className="mb-4">
                (2) Die Verpflichtung zur Vertraulichkeit gilt nicht für Informationen, die der empfangenden Partei bereits 
                bekannt waren, allgemein bekannt sind oder werden, ohne dass die empfangende Partei dies zu vertreten hat, oder 
                die von Dritten rechtmäßig ohne Verpflichtung zur Vertraulichkeit mitgeteilt werden.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">§ 11 Schlussbestimmungen</h2>
              <p className="mb-4">
                (1) Änderungen und Ergänzungen dieser AGB bedürfen der Textform. Dies gilt auch für die Änderung dieser 
                Textformklausel.
              </p>
              <p className="mb-4">
                (2) Sollten einzelne Bestimmungen dieser AGB unwirksam oder undurchführbar sein oder werden, so wird dadurch die 
                Wirksamkeit der übrigen Bestimmungen nicht berührt.
              </p>
              <p className="mb-4">
                (3) Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts.
              </p>
              <p className="mb-4">
                (4) Ausschließlicher Gerichtsstand für alle Streitigkeiten aus oder im Zusammenhang mit diesem Vertrag ist Berlin, 
                sofern der Kunde Kaufmann, juristische Person des öffentlichen Rechts oder öffentlich-rechtliches Sondervermögen 
                ist.
              </p>
            </section>

            <div className="mt-12 p-4 bg-gray-100 rounded-lg">
              <p className="text-sm text-gray-600">
                Stand: {new Date().toLocaleDateString('de-DE', { year: 'numeric', month: 'long' })}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Terms;